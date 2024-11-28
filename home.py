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
    
    st.markdown("# Início")
    st.sidebar.markdown("# Início")
    
    st.image(logo_path)
    
    #st.markdown("# EMORP - Intensiva E")
    #setor = ["EMORP - Intensiva E"]
    #df.query('SETOR in @setor')
    #st.dataframe(df[['SETOR','LEITO','PACIENTE','MEWS','BRADEN','MORSE']].query('SETOR in @setor'), use_container_width=True)

    #st.markdown("""
    #<style>
    #    .dataframe(
    #        height: 1000px;
    #        width: 100%;
    #    )
    #</style>
    #""", unsafe_allow_html=True)
    
    #st.dataframe(df[['SETOR','PACIENTE','MEWS']].query('SETOR in @setor'), use_container_width=True)
    #st.dataframe(df[['SETOR','PACIENTE','BRADEN']].query('SETOR in @setor'), use_container_width=True)
    #st.dataframe(df[['SETOR','PACIENTE','MORSE']].query('SETOR in @setor'), use_container_width=True)
    #st.dataframe(df[['SETOR','PACIENTE','FUGULIN']].query('SETOR in @setor'), use_container_width=True)
    #st.dataframe(df[['SETOR','PACIENTE','MARTINS']].query('SETOR in @setor'), use_container_width=True)
    #st.dataframe(df[['SETOR','PACIENTE','GLASGOW']].query('SETOR in @setor'), use_container_width=True)
    #st.dataframe(df[['SETOR','PACIENTE','PRECAUCAO']].query('SETOR in @setor'), use_container_width=True)