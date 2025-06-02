#26/11/2023
#@PLima
#HFS - PAINEL DE DIVERSOS DADOS E INDICADORES

import streamlit as st

import datetime
#Execucao:
#streamlit run inicio.py --server.port 8001

#Configurando pagina para exibicao em modo WIDE:
st.set_page_config(layout="wide",initial_sidebar_state="expanded")

# Caminho da sua imagem (ajuste conforme a sua estrutura de pastas)
logo_path = 'HSF_LOGO_-_1228x949_001.png'

def agora():
    agora = datetime.datetime.now()
    agora = agora.strftime("%Y-%m-%d %H-%M-%S")
    return str(agora)

if __name__ == "__main__":    
    print(f'{agora()} - __name__ == "__main__" - INÍCIO')
    st.logo(logo_path,size="large")
    #st.sidebar.markdown("# HOME")
    st.image(logo_path,width=400)
    st.write('\n\n\n\n')
    st.write('\n\n\n\n')
    st.write('## Dashboard - Escalas e GPT')
    st.write('\n\n\n\n')
    st.write('Destinado para exibição das escalas de Enfermagem no setor e o status do paciente na função GPT')
    st.write('\n\n\n\n')
    st.write('\n\n\n\n')
    st.write('Benefícios:')
    st.write('1 - Agilidade: Acesso rápido e fácil a informações cruciais para a tomada de decisões.')
    st.write('2 - Personalização: Adaptado às necessidades específicas de cada setor e equipe.')
    st.write('3 - Eficiência: Otimiza a assistência ao paciente e aumenta a produtividade da equipe.')
    st.write('4 - Precisão: Dados atualizados e confiáveis, diretamente do sistema TASY.')
    print(f'{agora()} - __name__ == "__main__" - FIM')
