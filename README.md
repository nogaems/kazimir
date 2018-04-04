# kazimir
Drawing diagrams (mostly for keyboard chords)

## Layout file specification

This is an example of the correct layout file. There are some necessary fields in the file and the lack of them will break the whole program working. Also, there are a few optional fields that you can omit.

(This spec is in early stage of design and with a high probability will be changed soon!)

```python

# required, contains diagrams that should be drawn
data = [
    {'Chord one': [[1, None, None], [0, 0, 0], [0, 0, 0]]},
    {'Chord two': [[1, None, None], [1, 0, 0], [0, 0, 0]]}
]

# optional, description of the entire picture
desc = 'Some text here'

# optional, if not set will be used a value from the utility CLI
output = '/path/to/the/desired/place'

# optional, if not set will be used default hardcoded values
config = {
    'bg': (255, 255, 255, 255),
    'font': 'terminus',
    'font_color': (0, 0, 0, 255),
    'cell_size': 16,  # The size of a side of the square in pixels
    'cell_bg': (102, 102, 102, 255),
    'cell_fg': (241, 194, 50, 255)
}
```

That's it. Fields that have been passed as None won't be drawn at all.

## Configuration file specification

I'll write about it later because at this moment I know nothing about it lol.
