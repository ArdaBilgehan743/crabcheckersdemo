import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// One fullscreen "film" pass: chromatic aberration + warm/teal split-tone grade
// + contrast/saturation + vignette + animated grain. Always outputs alpha = 1.
const GradeShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime: { value: 0 },
    uResolution: { value: new THREE.Vector2(1, 1) },
    uVignette: { value: 1.15 },
    uGrain: { value: 0.05 },
    uAberration: { value: 0.6 },
    uContrast: { value: 1.08 },
    uSaturation: { value: 0.92 },
  },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse;
    uniform float uTime, uVignette, uGrain, uAberration, uContrast, uSaturation;
    uniform vec2 uResolution;
    varying vec2 vUv;

    float hash(vec2 p) {
      return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
    }

    void main() {
      vec2 uv = vUv;
      vec2 c = uv - 0.5;
      float d = dot(c, c);

      // chromatic aberration (radial, stronger toward edges)
      vec2 off = c * uAberration * d * 0.06;
      vec3 col;
      col.r = texture2D(tDiffuse, uv + off).r;
      col.g = texture2D(tDiffuse, uv).g;
      col.b = texture2D(tDiffuse, uv - off).b;

      // split-tone: teal shadows, warm highlights
      float l = dot(col, vec3(0.299, 0.587, 0.114));
      vec3 cool = vec3(0.84, 0.95, 1.10);
      vec3 warm = vec3(1.08, 1.00, 0.86);
      col *= mix(cool, warm, smoothstep(0.0, 0.6, l));

      // contrast around mid grey
      col = (col - 0.5) * uContrast + 0.5;
      // saturation
      float g = dot(col, vec3(0.299, 0.587, 0.114));
      col = mix(vec3(g), col, uSaturation);

      // vignette
      float vig = 1.0 - uVignette * pow(clamp(d * 1.7, 0.0, 1.0), 1.25);
      col *= clamp(vig, 0.0, 1.0);

      // animated film grain
      float n = hash(uv * uResolution + fract(uTime) * 113.0) - 0.5;
      col += n * uGrain;

      gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
    }
  `,
};

export function detectQuality() {
  try {
    const coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
    const small = Math.min(window.innerWidth, window.innerHeight) < 720;
    const lowMem = typeof navigator !== 'undefined' && navigator.deviceMemory && navigator.deviceMemory <= 4;
    if (coarse || small || lowMem) return 'low';
  } catch (_e) {
    /* default high */
  }
  return 'high';
}

export function createPostFX(renderer, scene, camera, quality = 'high') {
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const target = new THREE.WebGLRenderTarget(size.x, size.y, {
    type: THREE.HalfFloatType,
    samples: quality === 'high' ? 4 : 0,
  });
  const composer = new EffectComposer(renderer, target);

  composer.addPass(new RenderPass(scene, camera));

  let bokeh = null;
  if (quality === 'high') {
    bokeh = new BokehPass(scene, camera, { focus: 6.5, aperture: 0.0006, maxblur: 0.006 });
    composer.addPass(bokeh);
  }

  const bloom = new UnrealBloomPass(
    new THREE.Vector2(size.x, size.y),
    quality === 'high' ? 0.55 : 0.42, // strength
    0.7, // radius
    0.82 // threshold — only the bulb / bright highlights bloom
  );
  composer.addPass(bloom);

  const grade = new ShaderPass(GradeShader);
  grade.uniforms.uResolution.value.set(size.x, size.y);
  grade.uniforms.uGrain.value = quality === 'high' ? 0.05 : 0.035;
  composer.addPass(grade);

  composer.addPass(new OutputPass());

  return {
    composer,
    bloom,
    bokeh,
    grade,
    quality,
    setSize(w, h) {
      composer.setSize(w, h);
      bloom.setSize(w, h);
      grade.uniforms.uResolution.value.set(w, h);
    },
    update(dt, focusDist) {
      grade.uniforms.uTime.value += dt;
      if (bokeh && focusDist) {
        const u = bokeh.uniforms.focus;
        u.value += (focusDist - u.value) * 0.1;
      }
    },
  };
}
