import json
import urllib.request
import ssl

RE_API_BASE = "https://www.robotevents.com/api/v2"
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzIiwianRpIjoiNWYzZGYyMTMwNmU2MDMwNThhZTg5MjYwYzZlMzYzZGFlZjU4MGQ0Njg5YzBkNjEyOTZiN2U3ZWU4MmY4NzQ0Mzk5YmFjZDkwNzA5YTdhNTciLCJpYXQiOjE3NzA4Mzg4MDUuNjI3MTkwMSwibmJmIjoxNzcwODM4ODA1LjYyNzE5MiwiZXhwIjoyNzE3NTIzNjA1LjYxNzk4MTksInN1YiI6IjExNzI1NSIsInNjb3BlcyI6W119.Z82UT9B8JCg-q75ar1nBVaXAFcQNfv5RdMjy47swGVdixePU77FZ8cb12hZifDefj4e49ontpY9lRmPo5nytB8EI1NDkEa4TEo1Lml-1FR0P73gq-IZIwxU3Ela-Gx8JUdMNFyAc4ZgdFKnCDxqHHyzzBvZupfdOtZV78KtyCERLmETgMGTNQcRhiT3E19Yvj2dkciLVOxSm1J_fFBdg4sbuRNLfsiizo1hRNwu-_OwePpJPP_nHjThou1Nd9kLsAj9R_aOnbvww_aDdOdYehmZkKGb_BTr_-oGPTUsRuEObY64G0EUTEY9l5pvm7sYPJCkX8rGRkQXW95C-OJL56hBAtfmJaiEuWi1zbZG44HjzV3MwYTKf2vU-ypKW9vVZJCODRZU1PDUeJnIbOsh3HjdVQC4oFhSDEhSBCwtA-ma8hfViwWhiY9qnhOjzrwEmbdAYjTrN_7_-aF_07500eIkwbYJ9KRZ5HFgN_4vXZCyeMft4jW6oOyJf9X9-9nTIrkPJHIXUQEKCSAofTYcR4KotFgZZrm0NfovHkyZop7zKGlxE78I4mAn1vAxIolOvNVlqi4kFl8S8R7-4F1DcM5YQbAmglq67wzlanerbmCckBQJ_NHGXrPnkPoNxQCaHkfsyVvTulip5r92GMvyesnqKt_vmJnCVrL_ycSps-kE"

def get_divs(sku):
    url = f"{RE_API_BASE}/events?sku[]={sku}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read().decode())
        event = data['data'][0]
        print(f"Event: {event['name']} (ID: {event['id']})")
        print(f"Divisions in payload: {event.get('divisions')}")
        
    url_divs = f"{RE_API_BASE}/events/{event['id']}/divisions"
    req = urllib.request.Request(url_divs, headers={'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read().decode())
        print(f"Divisions from /divisions endpoint: {data.get('data')}")

if __name__ == "__main__":
    get_divs("RE-V5RC-25-0166")
