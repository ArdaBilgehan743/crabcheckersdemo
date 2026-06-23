import './styles.css';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createPostFX, detectQuality } from './postfx.js';
import { chooseAiMove, chooseHint } from './ai.js';
import { CHARACTERS, MODIFIERS, STAKES, findByKey } from './content.js';
import {
  BOARD_SIZE,
  EMPTY,
  PLAYER_A,
  PLAYER_B,
  START_BOARD,
  applyMove,
  boardKey,
  cellName,
  checkWinner,
  countOpenThrees,
  legalMoves,
  moveNotation,
  opponent,
} from './rules.js';

const CELL = 1.04;
const BOARD_Y = 0.18;
const TOKEN_Y = 0.48;
const TABLE_Y = -0.14;
const LAMP_X = -3.05;
const LAMP_Z = -1.85;
const POINTER = new THREE.Vector2();
const TARGET = new THREE.Vector3(0, 0.35, 0);

const COLORS = {
  ink: 0x211812,
  paper: 0xf0d7ad,
  table: 0x6f4329,
  tableDark: 0x2c1c15,
  red: 0xc84f48,
  blue: 0x4c63cc,
  gold: 0xe3b45f,
  green: 0x61b77b,
  shell: 0xffe4ab,
};

const app = document.querySelector('#app');
const hud = document.querySelector('#hud');
const modal = document.querySelector('#modal');

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
app.append(renderer.domElement);

const QUALITY = detectQuality();

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x15100d);
scene.fog = new THREE.Fog(0x15100d, 11, 24);

const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 100);
let cameraMode = 'tactical';
let desiredCamera = cameraPose(cameraMode);
camera.position.copy(desiredCamera.position);
camera.lookAt(desiredCamera.target);

let postfx = null;
try {
  postfx = createPostFX(renderer, scene, camera, QUALITY);
} catch (error) {
  console.warn('Post-processing disabled:', error);
  postfx = null;
}

const raycaster = new THREE.Raycaster();
const interactive = [];
const boardGroup = new THREE.Group();
const tokenGroup = new THREE.Group();
const highlightGroup = new THREE.Group();
const avatarGroup = new THREE.Group();
scene.add(boardGroup, tokenGroup, highlightGroup, avatarGroup);

const game = {
  phase: 'menu',
  mode: 'solo',
  board: [...START_BOARD],
  current: PLAYER_A,
  selected: null,
  hint: null,
  moves: [],
  moveLog: [],
  positionCounts: new Map(),
  result: null,
  moving: null,
  aiTimer: 0,
  message: 'Choose a table.',
  run: {
    round: 1,
    shells: 0,
    wins: 0,
    stake: 'mid',
    playerChar: 'hat',
    rivalChar: 'bear',
    modifiers: [],
  },
  rewardChoices: [],
  roundMoveCounts: {
    [PLAYER_A]: 0,
    [PLAYER_B]: 0,
  },
  ui: {
    runOpen: false,
    movesOpen: false,
  },
};

const tokens = new Map();
const avatars = {};
let bearWantsFlinch = false;
let bearWantsSmug = false;
const clock = new THREE.Clock();
const gltfLoader = new GLTFLoader();
const runtimeModels = {
  avatars: {},
  tokens: {},
};

setupLights();
createRoom();
createBoard();
rebuildAvatars();
resetRound();
showMenu();
renderHud();
loadRuntimeModels();
animate();

window.addEventListener('resize', onResize);
renderer.domElement.addEventListener('pointerdown', onPointerDown);

if (import.meta.env?.DEV) {
  window.__crab = {
    game, avatars, tokens, play, directorTurn, directorRoundEnd, PLAYER_A, PLAYER_B,
    testMove() {
      const moves = legalMoves(game.board, game.current, game.run.modifiers);
      if (moves.length) startMove(moves[Math.floor(Math.random() * moves.length)]);
      return moves.length;
    },
  };
}

function setupLights() {
  // faint cool ambient so the room reads near-black, not flat grey
  const ambient = new THREE.AmbientLight(0x5d6b8a, 0.12);
  scene.add(ambient);

  // the hanging lamp: dominant warm key, soft deep shadows
  const lamp = new THREE.PointLight(0xffb066, 6.4, 24, 1.9);
  lamp.position.set(LAMP_X, 5.3, LAMP_Z);
  lamp.castShadow = true;
  lamp.shadow.mapSize.set(QUALITY === 'high' ? 2048 : 1024, QUALITY === 'high' ? 2048 : 1024);
  lamp.shadow.radius = 7;
  lamp.shadow.bias = -0.0004;
  scene.add(lamp);

  // warm key aimed at the board so POV stays readable while the room goes dark
  const boardKey = new THREE.SpotLight(0xffd6a0, 55, 18, Math.PI * 0.3, 0.55, 1.3);
  boardKey.position.set(0.6, 7.4, 2.4);
  boardKey.target.position.set(0, 0.18, 0);
  boardKey.castShadow = true;
  boardKey.shadow.mapSize.set(QUALITY === 'high' ? 2048 : 1024, QUALITY === 'high' ? 2048 : 1024);
  boardKey.shadow.radius = 6;
  boardKey.shadow.bias = -0.0004;
  scene.add(boardKey, boardKey.target);

  // cool rim from behind for character separation against the black
  const rim = new THREE.DirectionalLight(0x6f86c9, 0.5);
  rim.position.set(-5, 5.5, -7);
  scene.add(rim);
}

function createRoom() {
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(28, 22),
    new THREE.MeshStandardMaterial({ color: 0x211710, roughness: 0.95 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -1.18;
  floor.receiveShadow = true;
  scene.add(floor);

  const table = new THREE.Mesh(
    new THREE.BoxGeometry(9.4, 0.34, 8.8),
    new THREE.MeshStandardMaterial({ color: COLORS.table, roughness: 0.78, metalness: 0.02 })
  );
  table.position.y = TABLE_Y;
  table.castShadow = true;
  table.receiveShadow = true;
  scene.add(table);

  const cloth = new THREE.Mesh(
    new THREE.BoxGeometry(7.6, 0.06, 7.1),
    new THREE.MeshStandardMaterial({ color: 0x3a2218, roughness: 0.95 })
  );
  cloth.position.y = TABLE_Y + 0.21;
  cloth.receiveShadow = true;
  scene.add(cloth);

  const lampCord = new THREE.Mesh(
    new THREE.CylinderGeometry(0.018, 0.018, 3.8, 12),
    new THREE.MeshStandardMaterial({ color: COLORS.ink })
  );
  lampCord.position.set(LAMP_X, 4.75, LAMP_Z);
  scene.add(lampCord);

  const shade = new THREE.Mesh(
    new THREE.CylinderGeometry(0.58, 0.78, 0.55, 32, 1, true),
    new THREE.MeshStandardMaterial({
      color: 0x301f18,
      roughness: 0.65,
      side: THREE.DoubleSide,
    })
  );
  shade.position.set(LAMP_X, 3.05, LAMP_Z);
  shade.castShadow = true;
  scene.add(shade);

  const bulb = new THREE.Mesh(
    new THREE.SphereGeometry(0.18, 24, 16),
    new THREE.MeshBasicMaterial({ color: 0xffd888 })
  );
  bulb.position.set(LAMP_X, 2.9, LAMP_Z);
  scene.add(bulb);

  if (QUALITY === 'high') {
    // fake volumetric light shaft under the lamp
    const shaft = new THREE.Mesh(
      new THREE.ConeGeometry(1.7, 4.8, 32, 1, true),
      new THREE.MeshBasicMaterial({
        color: 0xffc890,
        transparent: true,
        opacity: 0.05,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      })
    );
    shaft.position.set(LAMP_X, 2.55, LAMP_Z);
    scene.add(shaft);

    // drifting dust motes catching the light
    const dustMaterial = new THREE.SpriteMaterial({
      color: 0xffe8c0,
      transparent: true,
      opacity: 0.3,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    for (let i = 0; i < 36; i += 1) {
      const mote = new THREE.Sprite(dustMaterial);
      mote.scale.setScalar(0.02 + Math.random() * 0.03);
      mote.position.set(
        LAMP_X + (Math.random() - 0.5) * 2.6,
        1.0 + Math.random() * 3.2,
        LAMP_Z + (Math.random() - 0.5) * 2.6
      );
      scene.add(mote);
    }
  }
}

function createBoard() {
  boardGroup.clear();
  interactive.length = 0;

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(CELL * BOARD_SIZE + 0.36, 0.26, CELL * BOARD_SIZE + 0.36),
    new THREE.MeshStandardMaterial({ color: 0x38241a, roughness: 0.82 })
  );
  base.position.y = BOARD_Y - 0.16;
  base.castShadow = true;
  base.receiveShadow = true;
  boardGroup.add(base);

  for (let row = 0; row < BOARD_SIZE; row += 1) {
    for (let col = 0; col < BOARD_SIZE; col += 1) {
      const square = new THREE.Mesh(
        new THREE.BoxGeometry(CELL * 0.96, 0.1, CELL * 0.96),
        new THREE.MeshStandardMaterial({
          color: (row + col) % 2 === 0 ? 0xefc99f : 0xb66d5c,
          roughness: 0.82,
        })
      );
      square.position.copy(cellPosition(row, col, BOARD_Y));
      square.userData = { type: 'cell', row, col };
      square.castShadow = true;
      square.receiveShadow = true;
      boardGroup.add(square);
      interactive.push(square);
    }
  }
}

function rebuildAvatars() {
  avatarGroup.clear();
  for (const key of Object.keys(avatars)) delete avatars[key];
  avatars[PLAYER_A] = createAvatar(findByKey(CHARACTERS, game.run.playerChar), PLAYER_A);
  avatars[PLAYER_B] = createAvatar(findByKey(CHARACTERS, game.run.rivalChar), PLAYER_B);
}

function createAvatar(character, player) {
  const side = player === PLAYER_A ? 1 : -1;
  const group = new THREE.Group();
  group.position.set(player === PLAYER_A ? -2.7 : 2.7, 0.04, side * 4.7);
  group.rotation.y = player === PLAYER_A ? Math.PI : 0;
  avatarGroup.add(group);
  const profile = avatarProfile(character.key, player);

  let mixer = null;
  let actions = null;
  let hasModel = false;
  if (runtimeModels.avatars[character.key]) {
    const inst = instantiateModel(runtimeModels.avatars[character.key]);
    inst.root.name = `${character.key}_blender_model`;
    inst.root.scale.setScalar(0.92);
    group.add(inst.root);
    mixer = inst.mixer;
    actions = inst.actions;
    hasModel = Boolean(inst.mixer);
  } else {
    const body = new THREE.Mesh(
      new THREE.CapsuleGeometry(0.42, 0.78, 8, 18),
      new THREE.MeshStandardMaterial({ color: profile.clothing, roughness: 0.72 })
    );
    body.scale.copy(profile.bodyScale);
    body.position.y = 0.8;
    body.castShadow = true;
    group.add(body);

    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.42, 26, 18),
      new THREE.MeshStandardMaterial({ color: profile.skin, roughness: 0.74 })
    );
    head.scale.copy(profile.headScale);
    head.position.y = 1.48;
    head.castShadow = true;
    group.add(head);

    if (character.key === 'bear') {
      addBearDetails(group);
    } else if (character.key === 'hat') {
      addHatDetails(group);
    } else if (character.key === 'diver') {
      addDiverDetails(group);
    } else if (character.key === 'widow') {
      addWidowDetails(group);
    } else {
      addLanternDetails(group);
    }
  }

  const shoulder = new THREE.Vector3(group.position.x + (player === PLAYER_A ? 0.36 : -0.36), 1.05, group.position.z - side * 0.2);
  const rest = new THREE.Vector3(group.position.x + (player === PLAYER_A ? 0.9 : -0.9), 0.72, group.position.z - side * 0.5);
  const hand = new THREE.Mesh(
    new THREE.SphereGeometry(0.13, 18, 12),
    new THREE.MeshStandardMaterial({ color: 0xf1d6b8, roughness: 0.8 })
  );
  hand.position.copy(rest);
  hand.castShadow = true;
  avatarGroup.add(hand);

  const arm = new THREE.Mesh(
    new THREE.CylinderGeometry(0.055, 0.07, 1, 12),
    new THREE.MeshStandardMaterial({ color: character.color, roughness: 0.72 })
  );
  arm.castShadow = true;
  avatarGroup.add(arm);

  const avatar = { group, hand, arm, shoulder, rest, character, bob: Math.random() * 4, mixer, actions, hasModel, currentName: null };
  if (mixer) mixer.addEventListener('finished', (event) => onAvatarActionFinished(avatar, event.action));
  if (hasModel) {
    hand.visible = false;
    arm.visible = false;
    if (actions.idle) play(avatar, 'idle', { loop: true, fade: 0 });
  }
  return avatar;
}

function avatarProfile(key, player) {
  if (key === 'bear') {
    return {
      clothing: 0x8c3d2f,
      skin: 0xcdbb95,
      bodyScale: new THREE.Vector3(1.28, 1.05, 1.05),
      headScale: new THREE.Vector3(1.24, 1.05, 1.08),
    };
  }
  if (key === 'diver') {
    return {
      clothing: 0x2f8f8b,
      skin: 0xd8c09c,
      bodyScale: new THREE.Vector3(0.88, 1.05, 0.88),
      headScale: new THREE.Vector3(0.96, 1.02, 0.96),
    };
  }
  if (key === 'widow') {
    return {
      clothing: 0x4b275f,
      skin: 0xd6b8c9,
      bodyScale: new THREE.Vector3(0.84, 1.18, 0.82),
      headScale: new THREE.Vector3(0.9, 1.0, 0.92),
    };
  }
  return {
    clothing: findByKey(CHARACTERS, key).color,
    skin: player === PLAYER_A ? 0xf0dfc6 : 0xd7c4af,
    bodyScale: new THREE.Vector3(0.94, 1.0, 0.9),
    headScale: new THREE.Vector3(0.96, 1.0, 0.96),
  };
}

function addBearDetails(group) {
  for (const x of [-0.26, 0.26]) {
    const ear = new THREE.Mesh(
      new THREE.SphereGeometry(0.14, 16, 10),
      new THREE.MeshStandardMaterial({ color: 0xf0dfc6, roughness: 0.75 })
    );
    ear.position.set(x, 1.82, 0.03);
    ear.castShadow = true;
    group.add(ear);
  }
  const muzzle = new THREE.Mesh(
    new THREE.SphereGeometry(0.18, 18, 12),
    new THREE.MeshStandardMaterial({ color: 0xe8d9ba, roughness: 0.8 })
  );
  muzzle.scale.set(1.35, 0.74, 0.9);
  muzzle.position.set(0, 1.39, 0.36);
  muzzle.castShadow = true;
  group.add(muzzle);
  addFace(group, 1.54, 0.36, 0.11, true);
  for (const x of [-0.42, 0.42]) {
    const paw = new THREE.Mesh(
      new THREE.SphereGeometry(0.14, 16, 10),
      new THREE.MeshStandardMaterial({ color: 0xcdbb95, roughness: 0.78 })
    );
    paw.scale.set(1.25, 0.8, 0.85);
    paw.position.set(x, 0.44, 0.34);
    paw.castShadow = true;
    group.add(paw);
  }
}

function addHatDetails(group) {
  const brim = new THREE.Mesh(
    new THREE.CylinderGeometry(0.58, 0.58, 0.08, 28),
    new THREE.MeshStandardMaterial({ color: 0x1d1714, roughness: 0.62 })
  );
  brim.position.y = 1.86;
  brim.castShadow = true;
  group.add(brim);
  const crown = new THREE.Mesh(
    new THREE.CylinderGeometry(0.34, 0.4, 0.42, 28),
    new THREE.MeshStandardMaterial({ color: 0x30241f, roughness: 0.62 })
  );
  crown.position.y = 2.08;
  crown.castShadow = true;
  group.add(crown);
  addFace(group, 1.5, 0.38, 0.09, false);
  const coatLine = new THREE.Mesh(
    new THREE.BoxGeometry(0.035, 0.62, 0.035),
    new THREE.MeshStandardMaterial({ color: 0x18100d, roughness: 0.8 })
  );
  coatLine.position.set(0, 0.83, 0.41);
  group.add(coatLine);
}

function addLanternDetails(group) {
  const glow = new THREE.Mesh(
    new THREE.SphereGeometry(0.16, 18, 12),
    new THREE.MeshBasicMaterial({ color: 0xffd878 })
  );
  glow.position.set(0.48, 1.18, 0.16);
  group.add(glow);
  addFace(group, 1.52, 0.36, 0.08, false);
  const hood = new THREE.Mesh(
    new THREE.TorusGeometry(0.44, 0.045, 8, 28),
    new THREE.MeshStandardMaterial({ color: 0x5c421d, roughness: 0.7 })
  );
  hood.position.set(0, 1.55, 0.02);
  hood.rotation.x = Math.PI / 2;
  group.add(hood);
}

function addDiverDetails(group) {
  addFace(group, 1.5, 0.38, 0.08, false);
  const goggles = new THREE.Group();
  for (const x of [-0.13, 0.13]) {
    const lens = new THREE.Mesh(
      new THREE.CylinderGeometry(0.105, 0.105, 0.025, 20),
      new THREE.MeshStandardMaterial({ color: 0x9ed7e0, roughness: 0.25, metalness: 0.08 })
    );
    lens.rotation.x = Math.PI / 2;
    lens.position.set(x, 1.55, 0.405);
    goggles.add(lens);
  }
  const strap = new THREE.Mesh(
    new THREE.BoxGeometry(0.42, 0.035, 0.035),
    new THREE.MeshStandardMaterial({ color: 0x1c302f, roughness: 0.8 })
  );
  strap.position.set(0, 1.55, 0.39);
  goggles.add(strap);
  group.add(goggles);
  const pearl = new THREE.Mesh(
    new THREE.SphereGeometry(0.09, 18, 12),
    new THREE.MeshStandardMaterial({ color: 0xf7e7b5, roughness: 0.32, metalness: 0.1 })
  );
  pearl.position.set(-0.32, 0.98, 0.42);
  group.add(pearl);
}

function addWidowDetails(group) {
  addFace(group, 1.5, 0.38, 0.075, false);
  const hair = new THREE.Mesh(
    new THREE.SphereGeometry(0.47, 24, 14),
    new THREE.MeshStandardMaterial({ color: 0x171017, roughness: 0.72 })
  );
  hair.scale.set(0.92, 1.08, 0.72);
  hair.position.set(0, 1.58, -0.02);
  hair.castShadow = true;
  group.add(hair);
  const veil = new THREE.Mesh(
    new THREE.ConeGeometry(0.5, 0.75, 24, 1, true),
    new THREE.MeshStandardMaterial({
      color: 0x2b1636,
      transparent: true,
      opacity: 0.46,
      roughness: 0.9,
      side: THREE.DoubleSide,
    })
  );
  veil.position.set(0, 1.62, 0.04);
  group.add(veil);
  const collar = new THREE.Mesh(
    new THREE.TorusGeometry(0.34, 0.035, 8, 28),
    new THREE.MeshStandardMaterial({ color: 0x181018, roughness: 0.8 })
  );
  collar.position.set(0, 1.08, 0.02);
  collar.rotation.x = Math.PI / 2;
  group.add(collar);
}

function addFace(group, y, z, eyeRadius, bearNose) {
  for (const x of [-0.13, 0.13]) {
    const eye = new THREE.Mesh(
      new THREE.SphereGeometry(eyeRadius, 12, 8),
      new THREE.MeshBasicMaterial({ color: 0x120d0b })
    );
    eye.scale.set(1, 0.72, 0.42);
    eye.position.set(x, y, z);
    group.add(eye);
  }
  const nose = new THREE.Mesh(
    new THREE.SphereGeometry(bearNose ? 0.07 : 0.04, 12, 8),
    new THREE.MeshBasicMaterial({ color: 0x120d0b })
  );
  nose.scale.set(bearNose ? 1.25 : 0.75, 0.75, 0.55);
  nose.position.set(0, y - 0.11, z + 0.025);
  group.add(nose);
}

function resetRound() {
  game.board = [...START_BOARD];
  game.current = PLAYER_A;
  game.selected = null;
  game.hint = null;
  game.moves = [];
  game.moveLog = [];
  game.result = null;
  game.positionCounts = new Map();
  game.moving = null;
  game.aiTimer = 0;
  game.roundMoveCounts = { [PLAYER_A]: 0, [PLAYER_B]: 0 };
  game.phase = 'playing';
  game.message = 'Player A to move.';
  recordPosition();
  rebuildTokens();
  updateHighlights();
  renderHud();
}

function rebuildTokens() {
  tokenGroup.clear();
  tokens.clear();
  const cells = interactive.filter((item) => item.userData?.type === 'cell');
  interactive.length = 0;
  interactive.push(...cells);
  for (let row = 0; row < BOARD_SIZE; row += 1) {
    for (let col = 0; col < BOARD_SIZE; col += 1) {
      const player = game.board[row][col];
      if (player === EMPTY) continue;
      const token = createCrabToken(player);
      token.position.copy(cellPosition(row, col, TOKEN_Y));
      token.userData = { type: 'piece', row, col, player };
      tokenGroup.add(token);
      tokens.set(`${row},${col}`, token);
      interactive.push(token);
    }
  }
}

function createCrabToken(player) {
  const color = player === PLAYER_A ? COLORS.red : COLORS.blue;
  const tokenKey = player === PLAYER_A ? 'red' : 'blue';
  if (runtimeModels.tokens[tokenKey]) {
    const inst = instantiateModel(runtimeModels.tokens[tokenKey]);
    inst.root.scale.setScalar(0.95);
    inst.root.animActor = { mixer: inst.mixer, actions: inst.actions, currentName: null };
    return inst.root;
  }
  const group = new THREE.Group();
  const body = new THREE.Mesh(
    new THREE.SphereGeometry(0.26, 26, 16),
    new THREE.MeshStandardMaterial({ color, roughness: 0.66 })
  );
  body.scale.set(1.15, 0.5, 0.92);
  body.castShadow = true;
  group.add(body);

  for (const x of [-0.22, 0.22]) {
    const eye = new THREE.Mesh(
      new THREE.SphereGeometry(0.045, 12, 8),
      new THREE.MeshBasicMaterial({ color: 0xfff4d6 })
    );
    eye.position.set(x, 0.12, -0.14);
    group.add(eye);
  }

  for (const x of [-0.38, 0.38]) {
    const claw = new THREE.Mesh(
      new THREE.SphereGeometry(0.11, 14, 10),
      new THREE.MeshStandardMaterial({ color, roughness: 0.7 })
    );
    claw.scale.set(1.15, 0.55, 0.78);
    claw.position.set(x, 0.02, -0.18);
    claw.castShadow = true;
    group.add(claw);
  }

  return group;
}

async function loadRuntimeModels() {
  const avatarFiles = {
    bear: '/models/avatar-bear.glb',
    hat: '/models/avatar-hat.glb',
    lantern: '/models/avatar-lantern.glb',
    diver: '/models/avatar-diver.glb',
    widow: '/models/avatar-widow.glb',
  };
  const tokenFiles = {
    red: '/models/crab-red.glb',
    blue: '/models/crab-blue.glb',
  };

  const avatarLoads = Object.entries(avatarFiles).map(async ([key, path]) => {
    const model = await loadOptionalModel(path);
    if (model) runtimeModels.avatars[key] = model;
  });
  const tokenLoads = Object.entries(tokenFiles).map(async ([key, path]) => {
    const model = await loadOptionalModel(path);
    if (model) runtimeModels.tokens[key] = model;
  });

  await Promise.all([...avatarLoads, ...tokenLoads]);
  rebuildAvatars();
  rebuildTokens();
  renderHud();
}

async function loadOptionalModel(path) {
  try {
    const gltf = await gltfLoader.loadAsync(path);
    gltf.scene.traverse((object) => {
      if (object.isMesh) {
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    return { scene: gltf.scene, animations: gltf.animations || [] };
  } catch (_error) {
    return null;
  }
}

function instantiateModel(entry) {
  const root = entry.scene.clone(true);
  root.traverse((object) => {
    if (object.isMesh) {
      object.castShadow = true;
      object.receiveShadow = true;
      if (object.material) object.material = object.material.clone();
    }
  });
  let mixer = null;
  const actions = {};
  if (entry.animations && entry.animations.length) {
    mixer = new THREE.AnimationMixer(root);
    for (const clip of entry.animations) {
      const action = mixer.clipAction(clip);
      action._clipName = clip.name;
      actions[clip.name] = action;
    }
  }
  return { root, mixer, actions };
}

// ---- animation performance director ----
function play(actor, name, { loop = false, fade = 0.2, hold = false } = {}) {
  if (!actor || !actor.actions) return null;
  const act = actor.actions[name];
  if (!act) return null;
  for (const [other, action] of Object.entries(actor.actions)) {
    if (other !== name && action.isRunning()) action.fadeOut(fade);
  }
  act.reset();
  act.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce, loop ? Infinity : 1);
  act.clampWhenFinished = !loop && (hold || name === 'win' || name === 'lose');
  act.enabled = true;
  act.setEffectiveWeight(1);
  act.fadeIn(fade);
  act.play();
  actor.currentName = name;
  return act;
}

function onAvatarActionFinished(avatar, action) {
  const name = action?._clipName;
  if (name === 'reach_start') play(avatar, 'reach_move', { hold: true });
  else if (name === 'reach_release') play(avatar, 'idle', { loop: true });
  else if (name === 'win' || name === 'lose' || name === 'draft_card') play(avatar, 'idle', { loop: true });
}

function directorMoveStart(move, player) {
  const token = tokens.get(`${move.row},${move.col}`);
  if (token?.animActor?.actions?.slide) play(token.animActor, 'slide', { loop: true, fade: 0.08 });
  const avatar = avatars[player];
  if (avatar?.hasModel && avatar.actions.reach_start) play(avatar, 'reach_start', {});
}

function directorMoveFinish(move, player) {
  const token = tokens.get(`${move.to.row},${move.to.col}`);
  if (token?.animActor?.actions?.hop_settle) play(token.animActor, 'hop_settle', {});
  const avatar = avatars[player];
  if (avatar?.hasModel && avatar.actions.reach_release) play(avatar, 'reach_release', {});
}

function directorTurn(player) {
  const avatar = avatars[player];
  if (avatar?.hasModel && avatar.actions.think) play(avatar, 'think', { loop: true });
}

function directorSelect(row, col) {
  const token = tokens.get(`${row},${col}`);
  if (token?.animActor?.actions?.threat_wiggle) play(token.animActor, 'threat_wiggle', { loop: true, fade: 0.1 });
}

function directorRoundEnd(result) {
  const bear = avatars[PLAYER_B];
  if (bear?.hasModel) {
    if (result === PLAYER_B && bear.actions.win) play(bear, 'win', {});
    else if (result === PLAYER_A && bear.actions.lose) play(bear, 'lose', {});
  }
  if (result === PLAYER_A || result === PLAYER_B) {
    for (const token of tokens.values()) {
      if (token.userData?.player === result && token.animActor?.actions?.win_pulse) {
        play(token.animActor, 'win_pulse', { loop: true, fade: 0.15 });
      }
    }
  }
}

function onPointerDown(event) {
  if (game.phase !== 'playing' || game.moving || modal.classList.contains('active')) return;
  if (game.mode === 'solo' && game.current === PLAYER_B) return;

  const rect = renderer.domElement.getBoundingClientRect();
  POINTER.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  POINTER.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(POINTER, camera);
  const hits = raycaster.intersectObjects(interactive, true);
  if (!hits.length) return;

  const root = findInteractiveRoot(hits[0].object);
  if (!root) return;

  if (root.userData.type === 'piece') {
    selectPiece(root.userData.row, root.userData.col);
  } else if (root.userData.type === 'cell') {
    clickCell(root.userData.row, root.userData.col);
  } else if (root.userData.type === 'destination') {
    startMove(root.userData.move);
  }
}

function findInteractiveRoot(object) {
  let current = object;
  while (current) {
    if (current.userData?.type) return current;
    current = current.parent;
  }
  return null;
}

function selectPiece(row, col) {
  if (game.board[row][col] !== game.current) return;
  game.selected = { row, col };
  game.hint = null;
  if (game.run.modifiers.includes('tide_lens')) {
    const tableHint = chooseHint(game.board, game.current, game.run.modifiers);
    if (tableHint?.row === row && tableHint?.col === col) {
      game.hint = tableHint;
    } else {
      game.hint = legalMoves(game.board, game.current, game.run.modifiers).find(
        (move) => move.row === row && move.col === col
      ) ?? null;
    }
  }
  directorSelect(row, col);
  updateHighlights();
  renderHud();
}

function clickCell(row, col) {
  if (!game.selected) return;
  const move = legalMoves(game.board, game.current, game.run.modifiers).find(
    (candidate) =>
      candidate.row === game.selected.row &&
      candidate.col === game.selected.col &&
      candidate.to.row === row &&
      candidate.to.col === col
  );
  if (move) startMove(move);
}

function startMove(move) {
  const token = tokens.get(`${move.row},${move.col}`);
  if (!token) return;
  const player = game.current;
  game.moving = {
    move,
    player,
    token,
    from: token.position.clone(),
    to: cellPosition(move.to.row, move.to.col, TOKEN_Y),
    progress: 0,
    duration: 1.05,
  };
  game.message = `${playerName(player)} moves ${moveNotation(move)}.`;
  game.selected = null;
  game.hint = null;
  directorMoveStart(move, player);
  updateHighlights();
  renderHud();
}

function finishMove() {
  const { move, player } = game.moving;
  const beforeThrees = countOpenThrees(game.board, player);
  game.board = applyMove(game.board, move);
  const afterThrees = countOpenThrees(game.board, player);
  if (player === PLAYER_A && game.run.modifiers.includes('chorus') && afterThrees > beforeThrees) {
    game.run.shells += 1;
  }
  if (player === PLAYER_A && game.run.modifiers.includes('center_reef') && isCenterCell(move.to)) {
    game.run.shells += 1;
  }
  if (player === PLAYER_A && game.run.modifiers.includes('corner_cache') && isCornerCell(move.to)) {
    game.run.shells += 2;
  }
  if (player === PLAYER_A && game.run.modifiers.includes('first_blood') && game.roundMoveCounts[PLAYER_A] === 0) {
    game.run.shells += 1;
  }
  game.roundMoveCounts[player] += 1;
  game.moveLog.unshift(`${playerName(player)} ${moveNotation(move)}`);
  game.moving = null;
  rebuildTokens();
  directorMoveFinish(move, player);

  const winner = checkWinner(game.board);
  if (winner) {
    endRound(winner);
    return;
  }

  game.current = opponent(game.current);
  const nextMoves = legalMoves(game.board, game.current, game.run.modifiers);
  if (nextMoves.length === 0) {
    endRound(opponent(game.current));
    return;
  }

  if (recordPosition()) {
    endRound('draw');
    return;
  }

  game.message = `${playerName(game.current)} to move.`;
  if (game.mode === 'solo' && game.current === PLAYER_B) {
    game.aiTimer = 0.65;
    directorTurn(PLAYER_B);
  }
  updateHighlights();
  renderHud();
}

function recordPosition() {
  const key = boardKey(game.board, game.current);
  const count = (game.positionCounts.get(key) ?? 0) + 1;
  game.positionCounts.set(key, count);
  return count >= 3;
}

function endRound(result) {
  game.result = result;
  game.phase = 'ended';
  updateHighlights();
  directorRoundEnd(result);
  if (result === 'draw') {
    game.message = 'Draw by repetition.';
    if (game.mode === 'solo' && game.run.modifiers.includes('soft_draw')) {
      game.run.shells += 1;
      game.run.round += 1;
      showRoundEnd('Soft Draw', 'Soft Draw paid one shell. Take a breath, then replay from a fresh table.');
    } else {
      showRoundEnd('Draw', 'The table locked into the same position three times.');
    }
  } else if (game.mode === 'solo' && result === PLAYER_A) {
    game.run.wins += 1;
    game.run.shells += 2;
    if (game.run.modifiers.includes('undertow')) game.run.shells += 1;
    if (game.run.modifiers.includes('pearl_bank')) game.run.shells += 2;
    if (game.run.modifiers.includes('black_pearl')) game.run.shells += 3;
    game.message = 'Round won. Draft a modifier.';
    showReward();
  } else if (game.mode === 'solo') {
    game.message = 'Run lost.';
    showRoundEnd('Run Over', `${findByKey(CHARACTERS, game.run.rivalChar).name} took the table.`);
  } else {
    game.message = `${playerName(result)} wins.`;
    showRoundEnd(`${playerName(result)} Wins`, 'The board belongs to them now.');
  }
  renderHud();
}

function updateHighlights() {
  highlightGroup.clear();
  const highlightObjects = interactive.filter((item) => item.userData?.type !== 'destination');
  interactive.length = 0;
  interactive.push(...highlightObjects);

  if (!game.selected) return;
  const moves = legalMoves(game.board, game.current, game.run.modifiers).filter(
    (move) => move.row === game.selected.row && move.col === game.selected.col
  );

  const selectedRing = createRing(0.47, COLORS.gold, 0.95);
  selectedRing.position.copy(cellPosition(game.selected.row, game.selected.col, TOKEN_Y + 0.02));
  highlightGroup.add(selectedRing);

  for (const move of moves) {
    const pad = new THREE.Mesh(
      new THREE.BoxGeometry(
        CELL * (game.run.modifiers.includes('wide_net') ? 1.08 : 0.86),
        0.08,
        CELL * (game.run.modifiers.includes('wide_net') ? 1.08 : 0.86)
      ),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })
    );
    pad.position.copy(cellPosition(move.to.row, move.to.col, TOKEN_Y + 0.02));
    pad.userData = { type: 'destination', move };
    highlightGroup.add(pad);
    interactive.push(pad);

    const ring = createRing(0.39, COLORS.green, 0.72);
    ring.position.copy(cellPosition(move.to.row, move.to.col, TOKEN_Y + 0.04));
    ring.userData = { type: 'destination', move };
    highlightGroup.add(ring);
    interactive.push(ring);
  }

  if (game.hint) {
    const hint = createRing(game.run.modifiers.includes('clean_cut') ? 0.62 : 0.5, COLORS.gold, 1);
    hint.position.copy(cellPosition(game.hint.to.row, game.hint.to.col, TOKEN_Y + 0.08));
    highlightGroup.add(hint);
  }
}

function createRing(radius, color, opacity) {
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(radius, 0.025, 8, 48),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity })
  );
  ring.rotation.x = Math.PI / 2;
  return ring;
}

function tickAi(dt) {
  if (game.phase !== 'playing' || game.mode !== 'solo' || game.current !== PLAYER_B || game.moving) return;
  game.aiTimer -= dt;
  if (game.aiTimer > 0) return;
  const stake = findByKey(STAKES, game.run.stake);
  const move = chooseAiMove(
    game.board,
    PLAYER_B,
    game.run.modifiers,
    stake.aiDepth + (game.run.modifiers.includes('black_pearl') ? 1 : 0)
  );
  if (move) startMove(move);
}

function updateMoveAnimation(dt) {
  if (!game.moving) return;
  const move = game.moving;
  move.progress += dt / move.duration;
  const t = moveSlideProgress(move.progress);
  move.token.position.lerpVectors(move.from, move.to, t);
  move.token.position.y = TOKEN_Y + Math.sin(t * Math.PI) * 0.16;
  if (move.progress >= 1) finishMove();
}

function updateAvatars(time) {
  for (const [player, avatar] of Object.entries(avatars)) {
    const active = game.current === player && game.phase === 'playing';
    avatar.group.position.y = Math.sin(time * 1.6 + avatar.bob) * 0.014 + (active ? 0.04 : 0);
    if (avatar.hasModel) continue;
    let target = avatar.rest.clone();
    if (game.moving?.player === player) {
      target = handTargetForMove(game.moving, avatar);
    }
    avatar.hand.position.lerp(target, game.moving?.player === player ? 0.68 : 0.2);
    setCylinderBetween(avatar.arm, avatar.shoulder, avatar.hand.position);
  }
}

function moveSlideProgress(progress) {
  return ease(clamp((progress - 0.24) / 0.62, 0, 1));
}

function handTargetForMove(move, avatar) {
  const progress = clamp(move.progress, 0, 1);
  const startTouch = move.from.clone();
  startTouch.y = 0.86;
  const follow = move.from.clone().lerp(move.to, moveSlideProgress(progress));
  follow.y = 0.88 + Math.sin(moveSlideProgress(progress) * Math.PI) * 0.08;

  if (progress < 0.24) {
    return avatar.rest.clone().lerp(startTouch, ease(progress / 0.24));
  }
  if (progress < 0.88) {
    return follow;
  }
  return follow.lerp(avatar.rest, ease((progress - 0.88) / 0.12));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function setCylinderBetween(mesh, start, end) {
  const midpoint = start.clone().add(end).multiplyScalar(0.5);
  const delta = end.clone().sub(start);
  mesh.position.copy(midpoint);
  mesh.scale.set(1, delta.length(), 1);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
}

function renderHud() {
  const stake = findByKey(STAKES, game.run.stake);
  const activeMods = game.run.modifiers.map((key) => findByKey(MODIFIERS, key));
  hud.innerHTML = `
    <section class="panel run-panel stack ${game.ui.runOpen ? 'open' : ''}">
      <div>
        <div class="eyebrow">Run</div>
        <h1>Tide ${game.run.round}</h1>
        <p class="muted">${stake.name} · ${stake.badge}</p>
      </div>
      <div class="pill-row">
        <span class="pill">${game.run.shells} shells</span>
        <span class="pill">${game.run.wins} wins</span>
        <span class="pill">${game.mode === 'solo' ? 'Solo' : 'Duel'}</span>
      </div>
      <div>
        <h2>Character</h2>
        <div class="card"><strong>${findByKey(CHARACTERS, game.run.playerChar).name}</strong><span class="muted">${findByKey(CHARACTERS, game.run.playerChar).title}</span></div>
      </div>
      <div>
        <h2>Modifiers</h2>
        <div class="card-list">
          ${activeMods.length ? activeMods.map((mod) => `<div class="card"><strong>${mod.name}</strong><span class="muted">${mod.text}</span></div>`).join('') : '<p class="muted">None yet.</p>'}
        </div>
      </div>
    </section>
    <section class="panel history-panel ${game.ui.movesOpen ? 'open' : ''}">
      <h2>Moves</h2>
      <div class="move-list">
        ${game.moveLog.slice(0, 10).map((line) => `<div class="muted">${line}</div>`).join('') || '<div class="muted">The table is waiting.</div>'}
      </div>
    </section>
    <nav class="bar control-bar">
      <span class="turn-chip"><strong>${playerName(game.current)}</strong><span>${game.message}</span></span>
      <button data-action="run" class="${game.ui.runOpen ? 'selected' : ''}">Run</button>
      <button data-action="moves" class="${game.ui.movesOpen ? 'selected' : ''}">Moves</button>
      <button data-action="camera">View: ${cameraLabel(cameraMode)}</button>
      <button data-action="hint" ${game.phase !== 'playing' ? 'disabled' : ''}>Hint</button>
      <button data-action="restart">New Round</button>
      <button data-action="menu">Menu</button>
    </nav>
  `;

  hud.querySelectorAll('[data-action]').forEach((button) => {
    button.addEventListener('click', () => handleHudAction(button.dataset.action));
  });
}

function handleHudAction(action) {
  if (action === 'menu') showMenu();
  if (action === 'run') {
    game.ui.runOpen = !game.ui.runOpen;
    if (game.ui.runOpen) game.ui.movesOpen = false;
    renderHud();
  }
  if (action === 'moves') {
    game.ui.movesOpen = !game.ui.movesOpen;
    if (game.ui.movesOpen) game.ui.runOpen = false;
    renderHud();
  }
  if (action === 'restart') resetRound();
  if (action === 'camera') {
    cameraMode = nextCameraMode(cameraMode);
    desiredCamera = cameraPose(cameraMode);
    renderHud();
  }
  if (action === 'hint') {
    if (game.phase !== 'playing' || game.current !== PLAYER_A) return;
    game.hint = chooseHint(game.board, PLAYER_A, game.run.modifiers);
    if (game.hint) {
      game.selected = { row: game.hint.row, col: game.hint.col };
      game.message = `Hint: ${cellName(game.hint.to.row, game.hint.to.col)} looks sharp.`;
      updateHighlights();
      renderHud();
    }
  }
}

function showMenu() {
  game.phase = 'menu';
  modal.classList.add('active');
  modal.innerHTML = `
    <div class="modal-card stack">
      <div>
        <div class="eyebrow">Crab Checkers 3D</div>
        <h1>Choose the table</h1>
      </div>
      <div class="choice-grid">
        ${CHARACTERS.map((character) => `
          <button class="choice ${game.run.playerChar === character.key ? 'selected' : ''}" data-character="${character.key}">
            <strong>${character.name}</strong>
            <span class="muted">${character.description}</span>
          </button>
        `).join('')}
      </div>
      <div class="choice-grid">
        ${STAKES.map((stake) => `
          <button class="choice ${game.run.stake === stake.key ? 'selected' : ''}" data-stake="${stake.key}">
            <strong>${stake.name}</strong>
            <span class="muted">${stake.badge} Stake</span>
          </button>
        `).join('')}
      </div>
      <div class="button-grid">
        <button class="${game.mode === 'solo' ? 'selected' : ''}" data-mode="solo">Solo Run</button>
        <button class="${game.mode === 'duel' ? 'selected' : ''}" data-mode="duel">Local Duel</button>
        <button data-start>Start</button>
      </div>
    </div>
  `;
  modal.querySelectorAll('[data-character]').forEach((button) => {
    button.addEventListener('click', () => {
      game.run.playerChar = button.dataset.character;
      game.run.rivalChar = 'bear';
      rebuildAvatars();
      showMenu();
    });
  });
  modal.querySelectorAll('[data-stake]').forEach((button) => {
    button.addEventListener('click', () => {
      game.run.stake = button.dataset.stake;
      showMenu();
    });
  });
  modal.querySelectorAll('[data-mode]').forEach((button) => {
    button.addEventListener('click', () => {
      game.mode = button.dataset.mode;
      showMenu();
    });
  });
  modal.querySelector('[data-start]').addEventListener('click', () => {
    modal.classList.remove('active');
    cameraMode = 'pov';
    desiredCamera = cameraPose(cameraMode);
    game.run.round = 1;
    game.run.wins = 0;
    game.run.shells = 0;
    game.run.modifiers = [];
    game.phase = 'playing';
    resetRound();
  });
  renderHud();
}

function showReward() {
  game.phase = 'reward';
  const owned = new Set(game.run.modifiers);
  const pool = MODIFIERS.filter((modifier) => !owned.has(modifier.key));
  const choiceCount = findByKey(STAKES, game.run.stake).rewardChoices + (game.run.modifiers.includes('redraw') ? 1 : 0);
  game.rewardChoices = shuffle(pool).slice(0, choiceCount);

  if (game.rewardChoices.length === 0) {
    modal.classList.add('active');
    modal.innerHTML = `
      <div class="modal-card stack">
        <div>
          <div class="eyebrow">Cache</div>
          <h1>The modifier tide is empty</h1>
          <p class="muted">You collected every modifier at the table. Take a cache reward and keep the run moving.</p>
        </div>
        <div class="choice-grid">
          <button class="choice" data-cache="shells">
            <strong>Shell Cache</strong>
            <span class="muted">Gain six shells and begin the next tide.</span>
          </button>
          <button class="choice" data-cache="pressure">
            <strong>Raise The Tide</strong>
            <span class="muted">Gain three shells, advance two tides, and keep climbing.</span>
          </button>
        </div>
      </div>
    `;
    modal.querySelectorAll('[data-cache]').forEach((button) => {
      button.addEventListener('click', () => {
        if (button.dataset.cache === 'pressure') {
          game.run.shells += 3;
          game.run.round += 2;
        } else {
          game.run.shells += 6;
          game.run.round += 1;
        }
        modal.classList.remove('active');
        resetRound();
      });
    });
    return;
  }

  modal.classList.add('active');
  modal.innerHTML = `
    <div class="modal-card stack">
      <div>
        <div class="eyebrow">Draft</div>
        <h1>Choose a table modifier</h1>
      </div>
      <div class="choice-grid">
        ${game.rewardChoices.map((modifier) => `
          <button class="choice" data-modifier="${modifier.key}">
            <strong>${modifier.name}</strong>
            <span class="muted">${modifier.text}</span>
          </button>
        `).join('')}
      </div>
    </div>
  `;
  modal.querySelectorAll('[data-modifier]').forEach((button) => {
    button.addEventListener('click', () => {
      game.run.modifiers.push(button.dataset.modifier);
      game.run.round += 1;
      modal.classList.remove('active');
      resetRound();
    });
  });
}

function isCenterCell(cell) {
  return (cell.row === 2 || cell.row === 3) && (cell.col === 2 || cell.col === 3);
}

function isCornerCell(cell) {
  return (cell.row === 0 || cell.row === BOARD_SIZE - 1) && (cell.col === 0 || cell.col === BOARD_SIZE - 1);
}

function showRoundEnd(title, text) {
  modal.classList.add('active');
  modal.innerHTML = `
    <div class="modal-card stack">
      <div>
        <div class="eyebrow">Table Result</div>
        <h1>${title}</h1>
        <p class="muted">${text}</p>
      </div>
      <div class="button-grid">
        <button data-reset-run>Restart Run</button>
        <button data-round>Replay Round</button>
      </div>
    </div>
  `;
  modal.querySelector('[data-reset-run]').addEventListener('click', () => {
    modal.classList.remove('active');
    showMenu();
  });
  modal.querySelector('[data-round]').addEventListener('click', () => {
    modal.classList.remove('active');
    resetRound();
  });
}

function cellPosition(row, col, y) {
  return new THREE.Vector3(
    (col - (BOARD_SIZE - 1) / 2) * CELL,
    y,
    (row - (BOARD_SIZE - 1) / 2) * CELL
  );
}

function playerName(player) {
  if (player === PLAYER_A) return 'Player A';
  if (player === PLAYER_B) return game.mode === 'solo' ? 'Rival' : 'Player B';
  return 'Draw';
}

function cameraPose(mode) {
  if (mode === 'tactical') {
    const narrow = window.innerWidth < 760 || window.innerWidth / window.innerHeight < 0.82;
    return {
      position: new THREE.Vector3(0, narrow ? 17.0 : 10.45, narrow ? 2.35 : 2.1),
      target: new THREE.Vector3(0, 0.18, 0),
    };
  }
  if (mode === 'table') {
    return { position: new THREE.Vector3(0, 7.7, 7.0), target: new THREE.Vector3(0, 0.2, 0) };
  }
  if (mode === 'opponent') {
    return { position: new THREE.Vector3(0.7, 4.5, -8.1), target: new THREE.Vector3(0, 0.36, 0.2) };
  }
  return { position: new THREE.Vector3(0, 2.15, 6.35), target: new THREE.Vector3(0, 1.0, -1.3) };
}

function cameraLabel(mode) {
  if (mode === 'tactical') return 'Tactical';
  if (mode === 'table') return 'Table';
  if (mode === 'opponent') return 'Rival';
  return 'Player';
}

function nextCameraMode(mode) {
  const modes = ['tactical', 'pov', 'table', 'opponent'];
  return modes[(modes.indexOf(mode) + 1) % modes.length];
}

function updateCamera() {
  camera.position.lerp(desiredCamera.position, 0.055);
  TARGET.lerp(desiredCamera.target, 0.07);
  if (cameraMode === 'pov') {
    const t = clock.elapsedTime;
    camera.position.x += Math.sin(t * 0.7) * 0.012 + Math.sin(t * 1.9) * 0.004;
    camera.position.y += Math.sin(t * 0.9 + 1.3) * 0.009;
  }
  camera.lookAt(TARGET);
}

function ease(t) {
  return 1 - (1 - t) * (1 - t);
}

function shuffle(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  const elapsed = clock.elapsedTime;
  tickAi(dt);
  updateMoveAnimation(dt);
  updateAvatars(elapsed);
  for (const avatar of Object.values(avatars)) avatar.mixer?.update(dt);
  for (const token of tokens.values()) token.animActor?.mixer?.update(dt);
  updateCamera();
  if (postfx) {
    postfx.update(dt, camera.position.distanceTo(TARGET));
    postfx.composer.render(dt);
  } else {
    renderer.render(scene, camera);
  }
}

function onResize() {
  renderer.setSize(window.innerWidth, window.innerHeight);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  postfx?.setSize(window.innerWidth, window.innerHeight);
  desiredCamera = cameraPose(cameraMode);
}
