export const CHARACTERS = [
  {
    key: 'bear',
    name: 'Patient Bear',
    title: 'Anchor',
    color: 0xc85b4f,
    description: 'Starts steady and turns blocks into pressure.',
  },
  {
    key: 'hat',
    name: 'The Hat',
    title: 'Trickster',
    color: 0x4c67c8,
    description: 'Loves strange lines and sideways tables.',
  },
  {
    key: 'lantern',
    name: 'Lantern Keeper',
    title: 'Seer',
    color: 0xdba642,
    description: 'Reads threats before they fully form.',
  },
  {
    key: 'diver',
    name: 'Pearl Diver',
    title: 'Gambler',
    color: 0x56a7a1,
    description: 'Plays fast, smiles late, and bets on narrow escapes.',
  },
  {
    key: 'widow',
    name: 'Velvet Widow',
    title: 'Closer',
    color: 0x8e4aa8,
    description: 'A precise rival who turns quiet boards into traps.',
  },
];

export const STAKES = [
  {
    key: 'easy',
    name: 'Low Tide',
    badge: 'Easy',
    aiDepth: 0,
    rewardChoices: 3,
  },
  {
    key: 'mid',
    name: 'Red Tide',
    badge: 'Mid',
    aiDepth: 2,
    rewardChoices: 3,
  },
  {
    key: 'hard',
    name: 'Black Tide',
    badge: 'Hard',
    aiDepth: 3,
    rewardChoices: 2,
  },
];

export const MODIFIERS = [
  {
    key: 'reef_drift',
    name: 'Reef Drift',
    type: 'movement',
    text: 'Crabs may stop on any empty square along a slide.',
  },
  {
    key: 'side_step',
    name: 'Side Step',
    type: 'movement',
    text: 'Unlock diagonal slides.',
  },
  {
    key: 'tide_lens',
    name: 'Tide Lens',
    type: 'vision',
    text: 'Hints mark the best destination for your selected crab.',
  },
  {
    key: 'chorus',
    name: 'Crab Chorus',
    type: 'score',
    text: 'Making three in a row earns an extra shell.',
  },
  {
    key: 'undertow',
    name: 'Undertow',
    type: 'tempo',
    text: 'After a win, start the next round with one bonus shell.',
  },
  {
    key: 'pearl_bank',
    name: 'Pearl Bank',
    type: 'economy',
    text: 'Round wins give two extra shells.',
  },
  {
    key: 'center_reef',
    name: 'Center Reef',
    type: 'economy',
    text: 'Moving into the center four squares earns one shell.',
  },
  {
    key: 'corner_cache',
    name: 'Corner Cache',
    type: 'economy',
    text: 'Moving into a corner earns two shells.',
  },
  {
    key: 'first_blood',
    name: 'First Blood Tide',
    type: 'tempo',
    text: 'Your first move each round earns one shell.',
  },
  {
    key: 'wide_net',
    name: 'Wide Net',
    type: 'movement',
    text: 'Destination targets become larger and easier to select.',
  },
  {
    key: 'clean_cut',
    name: 'Clean Cut',
    type: 'vision',
    text: 'Hint targets are marked with a larger golden ring.',
  },
  {
    key: 'redraw',
    name: 'Redraw Current',
    type: 'draft',
    text: 'Each draft offers one extra modifier choice.',
  },
  {
    key: 'black_pearl',
    name: 'Black Pearl',
    type: 'risk',
    text: 'Gain three shells after each win, but the rival thinks harder.',
  },
  {
    key: 'soft_draw',
    name: 'Soft Draw',
    type: 'safety',
    text: 'A repetition draw pays one shell instead of ending cold.',
  },
  {
    key: 'tide_chart',
    name: 'Tide Chart',
    type: 'vision',
    text: 'Long slides also offer a mid-route stopping point.',
  },
];

export function findByKey(items, key) {
  return items.find((item) => item.key === key) ?? items[0];
}
