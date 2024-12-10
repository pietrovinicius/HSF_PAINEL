--30/10/2024
--@PLima

-- RPA - PRESCR EM PDF - QUERY

--BACKUP:
/*

SELECT

    --APV.CD_SETOR_ATENDIMENTO AS CD_SETOR_ATENDIMENTO,
    --OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO) AS DS_SETOR,
    REPLACE(OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),'-',' ') AS DS_LEITO,
    --APV.NR_ATENDIMENTO AS NR_ATENDIMENTO,
    INITCAP(ABREVIA_NOME(obter_nome_pf(APV.CD_PESSOA_FISICA), 'A')) AS NM_PACIENTE,
    TO_CHAR(APV.DT_ENTRADA,'dd/mm/yyyy hh24:mi:ss') AS DT_ENTRADA,
    --MEWS
    (
        select
            TO_CHAR(em.DT_AVALIACAO,'dd/mm/yyyy hh24:mi:ss') || 
            ' > ' ||
            EM.qt_pontuacao|| 
            ' - '||
            decode(
                    em.QT_PONTUACAO,
                    0,'Baixo',
                    1,'Baixo',
                    2,'Baixo',
                    3,'Baixo',
                    4,'Baixo',
                    5,'Medio',
                    6,'Medio',
                    7,'Alto',
                    8,'Alto',
                    9,'Alto',
                    10,'Alto',
                    11,'Alto',
                    12,'Alto') 
            CLASSIFICACAO
        from ESCALA_MEWS EM, atendimento_paciente_v A
        where A.nr_atendimento = em.nr_atendimento
        and A.dt_alta is null
        AND A.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        AND EM.IE_SITUACAO = 'A'
        order by em.DT_LIBERACAO desc
        FETCH FIRST 1 ROWS ONLY
    )   AS MEWS,

    --BRADEN
    (
    select	
            TO_CHAR(AEB.DT_AVALIACAO,'dd/mm/yyyy hh24:mi:ss') ||
            ' > ' ||
            AEB.QT_PONTO || 
            ' - '|| 
            initcap(obter_resultado_braden(AEB.qt_ponto))
        from	atend_escala_braden AEB
        where  	(nr_atendimento	= APV.nr_atendimento)
        AND AEB.IE_SITUACAO = 'A'
        order by	1 desc
        FETCH FIRST 1 ROWS ONLY
    ) AS BRADEN,
    
    --morse
    (
        
        select	
            TO_CHAR(EMM.DT_AVALIACAO,'dd/mm/yyyy hh24:mi:ss') ||
            ' > ' ||
            EMM.qt_pontuacao|| 
            ' - '|| 
            initcap(obter_desc_escala_morse(qt_pontuacao))
        from 	escala_morse EMM
        where EMM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        AND EMM.IE_SITUACAO = 'A'
        order by	1 desc
        FETCH FIRST 1 ROWS ONLY
    ) AS MORSE,

    --fugulin
    (
        SELECT 
            TO_CHAR(GCAA.DT_AVALIACAO,'dd/mm/yyyy hh24:mi:ss') ||
            ' > ' ||
            (
                SELECT QT_PONTUACAO FROM GCA_ATENDIMENTO 
                WHERE NR_SEQUENCIA = (
                                        SELECT MAX(NR_SEQUENCIA) 
                                        FROM GCA_ATENDIMENTO 
                                        WHERE NR_ATENDIMENTO = AP.NR_ATENDIMENTO 
                                        AND IE_SITUACAO = 'A' 
                                        AND TRUNC(DT_AVALIACAO) = TRUNC(GCAA.DT_AVALIACAO))
            ) ||
            ' - '|| 
            (
                SELECT 
                --DS_GRADACAO 

                DECODE(
                    DS_GRADACAO,
                    'CM', 'Cuidados Mínimos',
                    'CI', 'Cuidados Intermediários',
                    'AD', 'Alta Dependência',
                    'SI', 'Cuidados Semi Intensivos',
                    'I', 'Cuidados Intensivos',
                    DS_GRADACAO
                )
                
                FROM GCA_GRADACAO 
                WHERE NR_SEQUENCIA = (
                                        SELECT NR_SEQ_GRADACAO 
                                        FROM GCA_ATENDIMENTO 
                                        WHERE NR_SEQUENCIA = 
                                            (
                                                SELECT MAX(NR_SEQUENCIA) 
                                                FROM GCA_ATENDIMENTO 
                                                WHERE NR_ATENDIMENTO = AP.NR_ATENDIMENTO 
                                                AND IE_SITUACAO = 'A' 
                                                AND TRUNC(DT_AVALIACAO) = TRUNC(GCAA.DT_AVALIACAO)
                                            )
                                    )
            )
        FROM ATENDIMENTO_PACIENTE AP
        INNER JOIN GCA_ATENDIMENTO GCAA ON GCAA.NR_ATENDIMENTO = AP.NR_ATENDIMENTO
        INNER JOIN GCA_GRADACAO GCAG ON GCAG.NR_SEQUENCIA = GCAA.NR_SEQ_GRADACAO
        WHERE GCAA.IE_SITUACAO = 'A'
        AND AP.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        order by GCAA.DT_AVALIACAO desc
        FETCH FIRST 1 ROWS ONLY
    ) AS FUGULIN,

    --martins
    (

        SELECT
            TO_CHAR(EEII.DT_AVALIACAO,'DD/MM/YY HH24:MI') ||
            ' > ' ||
            EEI.QT_PONTOS ||
            ' - '|| 
            substr(obter_desc_resul_score_flex_2(EEI.qt_pontos,EEI.nr_seq_escala),1,255)
        FROM ESCALA_EIF_II EEII
        INNER JOIN escala_eif_ii EEI ON (EEI.NR_SEQUENCIA = EEII.NR_SEQUENCIA)
        INNER JOIN SCORE_AVALIACAO_RESULT SAR ON (EEII.NR_SEQUENCIA = SAR.NR_SEQ_AVALIACAO)
        INNER JOIN MED_ITEM_AVALIAR MIA ON (MIA.NR_SEQUENCIA = SAR.NR_SEQ_ITEM)
        INNER JOIN MED_TIPO_AVALIACAO MTA ON (MTA.NR_SEQUENCIA = MIA.NR_SEQ_TIPO)
        WHERE EEII.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        AND SAR.DS_RESULTADO IS NOT NULL
        AND EEII.DT_LIBERACAO IS NOT NULL
        AND UPPER(MTA.DS_TIPO) LIKE '%MARTINS%'
        AND EEII.IE_SITUACAO = 'A'
        GROUP BY        EEII.DT_AVALIACAO,        EEI.qt_pontos,        EEI.nr_seq_escala
        ORDER BY EEII.DT_AVALIACAO DESC
        FETCH FIRST 1 ROWS ONLY


    ) AS MARTINS,

    --glasgow
    (

        select	
            TO_CHAR(AEI.dt_avaliacao,'dd/mm/yyyy hh24:mi:ss') ||
            ' > ' ||
            AEI.qt_glasgow ||
            ' - '|| 
            obter_resultado_glasgow(AEI.qt_glasgow)
        from	atend_escala_indice AEI
        WHERE 	obter_se_reg_lib_atencao(
                obter_pessoa_atendimento(
                    AEI.nr_atendimento,'C'), 
                    AEI.cd_pessoa_fisica, 
                    AEI.ie_nivel_atencao, 
                    AEI.nm_usuario, 374) = 'S'
        AND AEI.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        order bY AEI.dt_avaliacao desc
        FETCH FIRST 1 ROWS ONLY

    ) AS GLASGOW,

    --MEDICO RESPONSAVEL
    INITCAP(ABREVIA_NOME(obter_nome_medico(APV.cd_medico_resp,'N'), 'A')) MEDICO_RESPONSAVEL,

    (
        select distinct 
            INITCAP(ds_precaucao) ||
            ' - ' ||
            'Motivo: ' ||
            INITCAP(DS_MOTIVO)
        from atendimento_precaucao_v
        WHERE IE_SITUACAO = 'A'
        AND DT_INATIVACAO IS NULL
        order by DT_REGISTRO DESC
        FETCH FIRST 1 ROWS ONLY
    ) PRECAUCAO
FROM ATENDIMENTO_PACIENTE_V APV
LEFT JOIN prescr_medica PM ON (  PM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO )
LEFT JOIN prescr_mat_hor PH ON ( PH.NR_PRESCRICAO = PM.NR_PRESCRICAO)

--=============================================== REGRAS DE NEGOCIO: --===============================================
WHERE PH.dt_horario between SYSDATE - 1 and SYSDATE
AND APV.CD_SETOR_ATENDIMENTO = 56
GROUP BY 
    --APV.CD_SETOR_ATENDIMENTO,
    APV.CD_PESSOA_FISICA,
    APV.NR_ATENDIMENTO,
    APV.IE_STATUS_ATENDIMENTO,
    APV.cd_medico_resp,
    APV.DT_ENTRADA
ORDER BY 
    --OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO),
    OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),
    obter_nome_pf(APV.CD_PESSOA_FISICA)
*/


with SETORESW AS (
    
    SELECT DISTINCT
        SA.CD_SETOR_ATENDIMENTO cd,
        UPPER(SA.DS_SETOR_ATENDIMENTO) ds
    FROM SETOR_ATENDIMENTO  SA
    WHERE SA.IE_SITUACAO <> 'I'
    AND SA.CD_SETOR_ATENDIMENTO <> 171
    ORDER BY 2

)

SELECT
    APV.CD_SETOR_ATENDIMENTO AS SETOR_ATENDIMENTO,
    OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO) AS SETOR,
    REPLACE(OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),'-',' ') AS LEITO,
    --APV.NR_ATENDIMENTO AS ATEND,
    --INITCAP(ABREVIA_NOME(obter_nome_pf(APV.CD_PESSOA_FISICA), 'A')) AS PACIENTE,
    SUBSTR(obter_nome_pf(APV.CD_PESSOA_FISICA), 1, 1) || 
    SUBSTR(ABREVIA_NOME(obter_nome_pf(APV.CD_PESSOA_FISICA), 'A'), INSTR(ABREVIA_NOME(obter_nome_pf(APV.CD_PESSOA_FISICA), 'A'), ' ')) AS PACIENTE,
    TO_CHAR(APV.DT_ENTRADA,'dd/mm/yy hh24:mi') AS ENTRADA,
    --MEWS
    (
        select 
        em.QT_PONTUACAO as CLASSIFICACAO
        from ESCALA_MEWS EM, atendimento_paciente_v A
        where A.nr_atendimento = em.nr_atendimento
        and A.dt_alta is null
        AND A.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        AND EM.IE_SITUACAO = 'A'
        order by em.DT_LIBERACAO desc
        FETCH FIRST 1 ROWS ONLY
    )   AS MEWS,

    --BRADEN
    (
    select	
            initcap(obter_resultado_braden(AEB.qt_ponto))
        from	atend_escala_braden AEB
        where  	(nr_atendimento	= APV.nr_atendimento)
        AND AEB.IE_SITUACAO = 'A'
        order by	1 desc
        FETCH FIRST 1 ROWS ONLY
    ) AS BRADEN,
    
    --morse
    (
        
        select	
            initcap(obter_desc_escala_morse(qt_pontuacao))
        from 	escala_morse EMM
        where EMM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        AND EMM.IE_SITUACAO = 'A'
        order by	1 desc
        FETCH FIRST 1 ROWS ONLY
    ) AS MORSE,

    --fugulin
    (
        SELECT 
            (
                SELECT 
                --DS_GRADACAO 

                DECODE(
                    DS_GRADACAO,
                    'CM', 'Cuidados Mínimos',
                    'CI', 'Cuidados Intermediários',
                    'AD', 'Alta Dependência',
                    'SI', 'Cuidados Semi Intensivos',
                    'I', 'Cuidados Intensivos',
                    DS_GRADACAO
                )
                
                FROM GCA_GRADACAO 
                WHERE NR_SEQUENCIA = (
                                        SELECT NR_SEQ_GRADACAO 
                                        FROM GCA_ATENDIMENTO 
                                        WHERE NR_SEQUENCIA = 
                                            (
                                                SELECT MAX(NR_SEQUENCIA) 
                                                FROM GCA_ATENDIMENTO 
                                                WHERE NR_ATENDIMENTO = AP.NR_ATENDIMENTO 
                                                AND IE_SITUACAO = 'A' 
                                                AND TRUNC(DT_AVALIACAO) = TRUNC(GCAA.DT_AVALIACAO)
                                            )
                                    )
            )
        FROM ATENDIMENTO_PACIENTE AP
        INNER JOIN GCA_ATENDIMENTO GCAA ON GCAA.NR_ATENDIMENTO = AP.NR_ATENDIMENTO
        INNER JOIN GCA_GRADACAO GCAG ON GCAG.NR_SEQUENCIA = GCAA.NR_SEQ_GRADACAO
        WHERE GCAA.IE_SITUACAO = 'A'
        AND AP.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        order by GCAA.DT_AVALIACAO desc
        FETCH FIRST 1 ROWS ONLY
    ) AS FUGULIN,

    --martins
    (

        SELECT
            substr(obter_desc_resul_score_flex_2(EEI.qt_pontos,EEI.nr_seq_escala),1,255)
        FROM ESCALA_EIF_II EEII
        INNER JOIN escala_eif_ii EEI ON (EEI.NR_SEQUENCIA = EEII.NR_SEQUENCIA)
        INNER JOIN SCORE_AVALIACAO_RESULT SAR ON (EEII.NR_SEQUENCIA = SAR.NR_SEQ_AVALIACAO)
        INNER JOIN MED_ITEM_AVALIAR MIA ON (MIA.NR_SEQUENCIA = SAR.NR_SEQ_ITEM)
        INNER JOIN MED_TIPO_AVALIACAO MTA ON (MTA.NR_SEQUENCIA = MIA.NR_SEQ_TIPO)
        WHERE EEII.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        AND SAR.DS_RESULTADO IS NOT NULL
        AND EEII.DT_LIBERACAO IS NOT NULL
        AND UPPER(MTA.DS_TIPO) LIKE '%MARTINS%'
        AND EEII.IE_SITUACAO = 'A'
        GROUP BY        EEII.DT_AVALIACAO,        EEI.qt_pontos,        EEI.nr_seq_escala
        ORDER BY EEII.DT_AVALIACAO DESC
        FETCH FIRST 1 ROWS ONLY


    ) AS MARTINS,

    --glasgow
    (

        select	
            obter_resultado_glasgow(AEI.qt_glasgow)
        from	atend_escala_indice AEI
        WHERE 	obter_se_reg_lib_atencao(
                obter_pessoa_atendimento(
                    AEI.nr_atendimento,'C'), 
                    AEI.cd_pessoa_fisica, 
                    AEI.ie_nivel_atencao, 
                    AEI.nm_usuario, 374) = 'S'
        AND AEI.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        order bY AEI.dt_avaliacao desc
        FETCH FIRST 1 ROWS ONLY

    ) AS GLASGOW,

    --MEDICO RESPONSAVEL
    INITCAP(ABREVIA_NOME(obter_nome_medico(APV.cd_medico_resp,'N'), 'A')) MEDICO_RESPONSAVEL,

    (
        select distinct 
            INITCAP(ds_precaucao)
        from atendimento_precaucao_v
        WHERE IE_SITUACAO = 'A'
        AND DT_INATIVACAO IS NULL
        order by DT_REGISTRO DESC
        FETCH FIRST 1 ROWS ONLY
    ) PRECAUCAO,

    OBTER_GRUPOS_PACIENTE(APV.NR_ATENDIMENTO, APV.CD_PESSOA_FISICA) GRUPOS_PACIENTE,

    to_char(
            obter_prim_prescr_mat_hor_gpt(apv.nr_atendimento, apv.cd_pessoa_fisica, 'acmmeireles', '1')
            ,'dd/mm/yyyy hh24:mi:ss') prim_prescr_mat_hora_gpt,

    (
        --SEPARANDO:
        SELECT   
            ds_setor_atual || ' - ' || nm_paciente || ' - ' || ds_status_analise
        FROM	 
        table
        (
            gpt_utils_pck.get_pending_patients
            (   
            null,
            null,
            null,
            --to_date('27/11/2024 00:00:00',	'dd/mm/yyyy hh24:mi:ss'),
            --to_date('28/11/2024 23:59:59',	'dd/mm/yyyy hh24:mi:ss'),
            SYSDATE - 1 ,
            SYSDATE,
            null,
            '1',
            null,
            null,
            null,
            null,
            null,
            null,
            'N',
            'N',
            2,
            'N',
            'A',
            'N',
            null,
            'S',
            1,
            2,
            'N',
            'N',
            null,
            'N',
            'E',
            'N',
            'N',
            2,
            'N',
            'N',
            'A',
            'T',
            'N',
            'T',
            'E',
            null,
            2,
            'N',
            'S',
            'pvplima',
            null,
            0,
            '15',
            null,
            'N',
            null,
            null,
            null  
            )
        ) 
        WHERE 1 = 1
        AND NR_ATENDIMENTO = APV.NR_ATENDIMENTO
        FETCH FIRST 1 ROWS ONLY
    ) GPT_STATUS

FROM ATENDIMENTO_PACIENTE_V APV
LEFT JOIN prescr_medica PM ON (  PM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO )
LEFT JOIN prescr_mat_hor PH ON ( PH.NR_PRESCRICAO = PM.NR_PRESCRICAO)

--=============================================== REGRAS DE NEGOCIO: --===============================================
WHERE PH.dt_horario between SYSDATE - 1 and SYSDATE
AND APV.CD_SETOR_ATENDIMENTO = 58
GROUP BY 
    APV.CD_SETOR_ATENDIMENTO,
    APV.CD_PESSOA_FISICA,
    APV.NR_ATENDIMENTO,
    APV.IE_STATUS_ATENDIMENTO,
    APV.cd_medico_resp,
    APV.DT_ENTRADA
ORDER BY 
    OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO),
    OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),
    obter_nome_pf(APV.CD_PESSOA_FISICA)