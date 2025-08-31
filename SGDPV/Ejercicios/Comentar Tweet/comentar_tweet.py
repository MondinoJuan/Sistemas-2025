from requests_oauthlib import OAuth1
import requests


def comentar_tweet(usuario, tweet_id, comentario):
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(
        usuario["API_KEY"],
        usuario["API_SECRET"],
        usuario["ACCESS_TOKEN"],
        usuario["ACCESS_SECRET"],
    )
    data = {"text": comentario, "reply": {"in_reply_to_tweet_id": tweet_id}}
    response = requests.post(url, auth=auth, json=data)
    if response.status_code == 201:
        print(f"Comentario publicado por {usuario['nombre']} en el tweet {tweet_id}")
    else:
        print(f"Error al comentar por {usuario['nombre']}: {response.text}")


usuario = {
    "nombre": "",
    "API_KEY": "",
    "API_SECRET": "",
    "ACCESS_TOKEN": "",
    "ACCESS_SECRET": "",
}

tweet_id = "1960722316947517699"

comentario = "El Apache"

comentar_tweet(usuario, tweet_id, comentario)