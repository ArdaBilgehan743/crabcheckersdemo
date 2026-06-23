# Runtime Models

Place exported `.glb` files here. The Three.js prototype automatically uses matching runtime models when these files exist:

- `avatar-bear.glb`
- `avatar-hat.glb`
- `avatar-lantern.glb`
- `crab-red.glb`
- `crab-blue.glb`
- `table-room.glb`
- `board-6x6.glb`

Keep `.blend` source files in `assets/blender/`.

Regenerate the current asset set with:

```bash
npm run assets:blender
```
