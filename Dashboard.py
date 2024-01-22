# Import necessary libraries
import streamlit as st
import pandas as pd
# First, import the elements you need

from streamlit_elements import elements, mui, html

# Create a frame where Elements widgets will be displayed.
#
# Elements widgets will not render outside of this frame.
# Native Streamlit widgets will not render inside this frame.
#
# elements() takes a key as parameter.
# This key can't be reused by another frame or Streamlit widget.

with elements("new_element"):

    # Let's create a Typography element with "Hello world" as children.
    # The first step is to check Typography's documentation on MUI:
    # https://mui.com/components/typography/
    #
    # Here is how you would write it in React JSX:
    #
    # <Typography>
    #   Hello world
    # </Typography>

    mui.Typography("Hello world")

with elements("multiple_children"):

    # You have access to Material UI icons using: mui.icon.IconNameHere
    #
    # Multiple children can be added in a single element.
    #
    # <Button>
    #   <EmojiPeople />
    #   <DoubleArrow />
    #   Hello world
    # </Button>

    mui.Button(
        mui.icon.EmojiPeople,
        mui.icon.DoubleArrow,
        "Button with multiple children"
    )

    # You can also add children to an element using a 'with' statement.
    #
    # <Button>
    #   <EmojiPeople />
    #   <DoubleArrow />
    #   <Typography>
    #     Hello world
    #   </Typography>
    # </Button>

    with mui.Button:
        mui.icon.EmojiPeople()
        mui.icon.DoubleArrow()
        mui.Typography("Button with multiple children")

