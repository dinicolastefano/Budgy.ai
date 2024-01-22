# Import necessary libraries
import streamlit as st
import pandas as pd
import streamlit as st

import streamlit as st

row1 = st.columns(4)
row2 = st.columns(1)
row3= st.columns(2)

for col in row1 :
    tile = col.container(height=100)
    tile.title(":balloon:")
