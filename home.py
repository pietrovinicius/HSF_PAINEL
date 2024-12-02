#26/11/2023
#@PLima
#HFS - PAINEL DE DIVERSOS DADOS E INDICADORES

import streamlit as st
import pandas as pd
import numpy as np
import os
import oracledb
import pandas as pd

import plotly.express as px

# Caminho da sua imagem (ajuste conforme a sua estrutura de pastas)
logo_path = 'HSF_LOGO_-_1228x949_001.png'

if __name__ == "__main__":    
    st.logo(logo_path,size="large")
    st.sidebar.markdown("# Home")
    st.image(logo_path)