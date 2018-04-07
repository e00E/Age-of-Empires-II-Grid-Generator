import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Default spacing is 51 because in the HD edition tiles are 53 pixels and have two pixels overlap
# with their neighbours.
def make_grid_mask(alpha=1.0, width=1, spacing=51, size=512):
    assert alpha >= 0.0 and alpha <= 1.0
    if alpha == 1.0:
        mode = "1"
        background = 1
        fill = 0
    else:
        mode = "L"
        background = 255
        fill = round(255 * (1 - alpha))
    image = Image.new(mode, (size, size), background)
    d = ImageDraw.Draw(image)
    # The eleventh element [size] is intentional:
    # Width wider than 1 lines the `line` function will draw the line centered on the given
    # coordinates, so half of the very first line would be out of bounds and thus not visible.
    # By adding [size] we will get the other half of the line at the end of the image.
    coordinates = [spacing * i for i in range(10)] + [size]
    for x in coordinates:
        d.line([(x, 0), (x, size - 1)], fill=fill, width=width)
    for y in coordinates:
        d.line([(0, y), (size - 1, y)], fill=fill, width=width)
    return image

def is_valid_directory(path):
    return path.exists() and path.is_dir()

description = '''
Add grid lines to the terrain textures of Age of Empires II.

Read the readme for more information.
'''

def main():
    parser = argparse.ArgumentParser(prog='Age of Empires II Grid Generator', description=description)
    parser.add_argument('--game-dir', required=True, help='Installation directory of the game.')
    parser.add_argument('--mod-dir', help='Installation directory of an existing mod to add grid lines to instead of the base game.')
    parser.add_argument('--alpha', type=float, default=0.2, help='Degree of opacity of the grid lines. 1.0 means totally opaque and 0.0 totally transparent. Default: 0.2')
    parser.add_argument('--width', type=int, default=2, help='Width of the grid lines in pixels. Default: 2')
    parser.add_argument('--color', type=int, nargs=3, default=[0, 0, 0], help='Three integers between 0 and 255 representing a color in RGB format. Default: 0 0 0 (black)')
    parser.add_argument('--preview', action='store_const', const=True, default=False, help='Show a preview instead of creating the files.')
    parser.add_argument('--clean', action='store_const', const=True, default=False, help='Clean the installation directory of the grid terrain before running. Useful to delete remnants of previous runs when using it on a different mod.')
    args = parser.parse_args()


    path = Path('resources', '_common', 'terrain', 'textures')

    game_directory = Path(args.game_dir)

    if not is_valid_directory(game_directory):
        print('Game directory is invalid.')
        return
    if args.mod_dir != None:
        source_directory = Path(args.mod_dir)
        if not is_valid_directory(source_directory):
            print('Mod directory is invalid.')
            return
        source_directory = source_directory / path
        if not is_valid_directory(source_directory):
            print('Mod does not contain any terrain textures.')
            return
    else:
        source_directory = game_directory / path
        if not is_valid_directory(source_directory):
            print('Game does not contain any terrain textures.')
            return

    mod_name = 'Grid Generator'
    if not args.preview:
        installation_directory = game_directory / 'mods' / mod_name / path
        installation_directory.mkdir(parents=True, exist_ok=True)
        if(args.clean):
            for path in installation_directory.glob('*.png'): path.unlink()
        print('Processing textures from', source_directory, 'to', installation_directory)
    else:
        print('Showing preview')

    mask = make_grid_mask(args.alpha, args.width)
    grid_masks = {}
    # For blending the images together we need to have matching `modes` in PIL terminology.
    # We map modes to grid images in this dict so we can avoid recreating them unnecessarily.
    grid_images = {}
    for path in source_directory.glob('*.png'):
        if not path.is_file(): continue

        if not args.preview: print("Writing", path.name)
        original = Image.open(path)

        mode = original.mode
        # It is not  clear how to handle the color of the grid in other modes so we convert
        # them to RGB.
        if not mode in ['RGB', 'RGBA']:
            original = original.convert('RGB')
            mode = 'RGB'

        # As far as I know there is no reason to have textures of a different size than 512x512
        # as they will always be rescaled by the game. Some mods still use other resolutions
        # so we resize them before applying the grid.
        # If this was not the case we would have to generate a different grid mask for each resolution.
        if original.size != (512, 512):
            print(path, "should have dimensions of (512, 512) but actually has", original.size,
                    ". Will be resized.")
            original = original.resize((512, 512), Image.LANCZOS)

        if not mode in grid_images:
            grid_images[mode] = Image.new(mode, (512, 512), tuple(args.color))
        grid = grid_images[mode]

        result = Image.composite(original, grid, mask)

        if args.preview:
            result.rotate(45, resample=Image.LANCZOS, expand=True).show()
            return
        else:
            result.save(installation_directory / path.name)
    print('Done')

if __name__ == '__main__':
    main()
