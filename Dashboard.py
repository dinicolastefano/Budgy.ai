# Import necessary libraries
import streamlit as st
import pandas as pd
import streamlit as st

import streamlit as st

row1 = st.columns(3)
row2 = st.columns(3)

for col in row1 + row2:
    tile = col.container(height=120)
    tile.title(":balloon:")
