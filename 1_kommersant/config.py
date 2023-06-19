url_to_scrap = "https://www.kommersant.ru/lenta?from=all_lenta"

# url_to_download = "https://kycbase.io/parsers/api/articles/bulk/"
url_to_download = "https://kycbase.io/parsers/api/articles/"

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "accept": "application/json, text/plain, text/html, */*"
}


POSTGRES_USER = 'postgres'
POSTGRES_PASSWORD = 'password'
POSTGRES_HOSTNAME = 'postgres_kommersant'
# POSTGRES_HOSTNAME = '127.0.0.1'
POSTGRES_PORT = 5432
POSTGRES_DB = 'db_previous_kommersant'
