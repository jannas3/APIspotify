import pandas as pd
import requests
import base64
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Função para gerar o token de autenticação
def get_access_token(client_id, client_secret):
    string = f"{client_id}:{client_secret}"
    base64_string = base64.b64encode(string.encode("ascii")).decode("ascii")
    url = 'https://accounts.spotify.com/api/token'
    headers = {'Authorization': f'Basic {base64_string}', 'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'grant_type': 'client_credentials'}
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        st.error(f"Erro na autenticação: {response.status_code} - {response.json()}")
        return None

# Função para buscar os dados dos álbuns
def get_album_data(access_token, album_ids, market="BR"):
    url = f'https://api.spotify.com/v1/albums?ids={album_ids}&market={market}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erro ao buscar dados dos álbuns: {response.status_code} - {response.json()}")
        return None

# Função para obter dados das faixas
def get_tracks_data(access_token, track_ids):
    track_url = f'https://api.spotify.com/v1/tracks?ids={",".join(track_ids)}'
    headers = {'Authorization': f'Bearer {access_token}'}
    track_response = requests.get(track_url, headers=headers)
    return track_response

# Credenciais da API do Spotify
client_id = '85bb7657643f472e8b0a85eef079ba77'
client_secret = '55fbb0a3af614288b0168b2bceba5cd0'

# Streamlit app
st.title("Análise Comparativa de Álbuns - Marília Mendonça 🎵")

# Obter token de autenticação
access_token = get_access_token(client_id, client_secret)

if access_token:
    # IDs dos álbuns de Marília Mendonça
    album_options = {
        "Festa das Patroas": "4IzsHOBctS66OP3dHXTJsG",
        "Todos os Cantos": "4HpiwfnQvs867JNWeLy1vr"
    }
    selected_albums = st.sidebar.multiselect(
        "Selecione os álbuns para comparação:",
        list(album_options.keys()),
        default=["Festa das Patroas", "Todos os Cantos"]
    )

    if selected_albums:
        selected_ids = ",".join([album_options[album] for album in selected_albums])
        data = get_album_data(access_token, selected_ids)

        if data:
            # Preparar dados gerais dos álbuns
            album_info = []
            for album in data["albums"]:
                tracks = album['tracks']['items']
                album_name = album['name']
                artist_name = album['artists'][0]['name']
                total_tracks = len(tracks)
                total_duration = sum([track['duration_ms'] for track in tracks]) / 60000  # em minutos
                
                album_info.append({
                    "Álbum": album_name,
                    "Artista": artist_name,
                    "Total de Faixas": total_tracks,
                    "Duração Total (min)": total_duration
                })

            album_df = pd.DataFrame(album_info)

            # Exibir dados gerais dos álbuns
            st.subheader("Informações Gerais dos Álbuns")
            st.dataframe(album_df)

            # Dados dos álbuns já obtidos
            album_1 = data["albums"][0]
            album_2 = data["albums"][1]

            # Faixas de cada álbum
            tracks_album_1 = album_1['tracks']['items']
            tracks_album_2 = album_2['tracks']['items']

            # Preparar listas para faixas, popularidade e duração
            track_names_1 = [track['name'] for track in tracks_album_1]
            track_names_2 = [track['name'] for track in tracks_album_2]

            # Obter IDs das faixas para consultar as popularidades e durações
            track_ids_1 = [track['id'] for track in tracks_album_1]
            track_ids_2 = [track['id'] for track in tracks_album_2]

            track_response = get_tracks_data(access_token, track_ids_1 + track_ids_2)

            if track_response.status_code == 200:
                track_data = track_response.json()

                # Popularidade e duração para o álbum 1
                popularity_1 = [track['popularity'] for track in track_data['tracks'][:len(track_names_1)]]
                durations_1 = [track['duration_ms'] / 1000 for track in track_data['tracks'][:len(track_names_1)]]  # Duração em segundos

                # Popularidade e duração para o álbum 2
                popularity_2 = [track['popularity'] for track in track_data['tracks'][len(track_names_1):]]
                durations_2 = [track['duration_ms'] / 1000 for track in track_data['tracks'][len(track_names_1):]]  # Duração em segundos

                # Gráfico 1: Correlação entre popularidade e duração
                st.subheader('Correlação entre Popularidade e Duração das Faixas')
                plt.figure(figsize=(10, 6))
                plt.scatter(durations_1, popularity_1, label="Álbum 1", color='blue', alpha=0.6)
                plt.scatter(durations_2, popularity_2, label="Álbum 2", color='orange', alpha=0.6)
                plt.title('Correlação entre Popularidade e Duração das Faixas')
                plt.xlabel('Duração (segundos)')
                plt.ylabel('Popularidade')
                plt.legend()
                st.pyplot(plt)
                
                # Adicionando legenda interpretativa
                st.markdown("""
                **Interpretação:** Neste gráfico de dispersão, podemos observar a relação entre a popularidade das faixas e a duração das músicas.
                As faixas de ambos os álbuns seguem padrões distintos, com algumas faixas mais curtas apresentando maior popularidade, enquanto outras são mais longas e têm menor popularidade.
                O álbum 2 parece ter mais faixas curtas e populares.
                """)

                # Média de popularidade por álbum
                avg_pop_album_1 = sum(popularity_1) / len(popularity_1) if popularity_1 else 0
                avg_pop_album_2 = sum(popularity_2) / len(popularity_2) if popularity_2 else 0
                avg_pop_geral = (avg_pop_album_1 + avg_pop_album_2) / 2

                albuns = ['Álbum 1', 'Álbum 2', 'Média Geral']
                popularidade_album = [avg_pop_album_1, avg_pop_album_2, avg_pop_geral]

                # Gráfico 2: Popularidade média por álbum
                st.subheader('Popularidade Média das Faixas por Álbum e Média Geral')
                plt.figure(figsize=(10, 6))
                sns.barplot(x=albuns, y=popularidade_album, hue=albuns, palette='muted')
                plt.title('Popularidade Média das Faixas por Álbum e Média Geral', fontsize=16)
                plt.xlabel('Álbum', fontsize=14)
                plt.ylabel('Popularidade Média', fontsize=14)
                st.pyplot(plt)
                
                # Adicionando legenda interpretativa
                st.markdown("""
                **Interpretação:** Este gráfico de barras compara a popularidade média das faixas entre os dois álbuns.
                O Álbum 2 apresenta uma popularidade média ligeiramente superior, o que pode sugerir que suas faixas têm mais apelo geral, talvez devido a parcerias de destaque.
                A média geral também está bem equilibrada entre os álbuns.
                """)

                # Gráfico 3: Faixas mais populares (Ordenadas)
                faixas_1_sorted = [faixa for _, faixa in sorted(zip(popularity_1, track_names_1), reverse=True)]
                popularity_1_sorted = sorted(popularity_1, reverse=True)

                faixas_2_sorted = [faixa for _, faixa in sorted(zip(popularity_2, track_names_2), reverse=True)]
                popularity_2_sorted = sorted(popularity_2, reverse=True)

                df_1 = pd.DataFrame({
                    'Faixa': faixas_1_sorted,
                    'Popularidade': popularity_1_sorted
                })

                df_2 = pd.DataFrame({
                    'Faixa': faixas_2_sorted,
                    'Popularidade': popularity_2_sorted
                })

                # Gráfico para o Álbum 1
                st.subheader(f'Faixas Mais Populares - {album_1["name"]}')
                plt.figure(figsize=(10, 6))
                plt.barh(df_1['Faixa'], df_1['Popularidade'], color='lightcoral')
                plt.xlabel('Popularidade')
                plt.ylabel('Faixa')
                plt.gca().invert_yaxis()  # Para que a faixa mais popular apareça no topo
                st.pyplot(plt)
                
                # Adicionando legenda interpretativa
                st.markdown(f"""
                **Interpretação:** O gráfico acima mostra as faixas mais populares do álbum **{album_1["name"]}**.
                As faixas mais populares geralmente têm um maior apelo com o público, e isso pode indicar o estilo ou a colaboração com outros artistas que geraram mais interesse.
                """)

                # Gráfico para o Álbum 2
                st.subheader(f'Faixas Mais Populares - {album_2["name"]}')
                plt.figure(figsize=(10, 6))
                plt.barh(df_2['Faixa'], df_2['Popularidade'], color='lightblue')
                plt.xlabel('Popularidade')
                plt.ylabel('Faixa')
                plt.gca().invert_yaxis()  # Para que a faixa mais popular apareça no topo
                st.pyplot(plt)

                # Adicionando legenda interpretativa
                st.markdown(f"""
                **Interpretação:** O gráfico acima mostra as faixas mais populares do álbum **{album_2["name"]}**.
                Assim como no álbum anterior, as faixas mais populares podem indicar o apelo maior com o público, e o estilo da música, bem como as parcerias, podem ter influência significativa na popularidade.
                """)

                # Destaques
                st.subheader("🎶 Destaques")
                # Faixa mais popular
                most_popular_track_1 = track_names_1[popularity_1.index(max(popularity_1))]
                most_popular_track_2 = track_names_2[popularity_2.index(max(popularity_2))]
                most_popular_track = most_popular_track_1 if max(popularity_1) > max(popularity_2) else most_popular_track_2
                st.markdown(f"🎶 **Faixa mais popular:** {most_popular_track} (Álbum: {album_1['name'] if most_popular_track == most_popular_track_1 else album_2['name']}, Popularidade: {max(popularity_1) if most_popular_track == most_popular_track_1 else max(popularity_2)})")

                # Faixa mais longa
                longest_track_1 = max(tracks_album_1, key=lambda x: x['duration_ms'])
                longest_track_2 = max(tracks_album_2, key=lambda x: x['duration_ms'])
                longest_track = longest_track_1 if longest_track_1['duration_ms'] > longest_track_2['duration_ms'] else longest_track_2
                st.markdown(f"⏳ **Faixa mais longa:** {longest_track['name']} (Álbum: {album_1['name'] if longest_track == longest_track_1 else album_2['name']}, Duração: {longest_track['duration_ms'] / 60000:.2f} minutos)")
                
            else:
                st.error("Erro ao buscar dados das faixas.")
else:
    st.error("Falha na autenticação. Verifique as credenciais.")
