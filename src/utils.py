import json
import random
import pyfiglet
from requests import request
from PIL import Image, ImageDraw




def is_admin(user_id, users):
    
    if str(user_id) in users:
        return True
    return False

def get_id(message):
    return message.from_user.id


def get_hosts(method, url, headers, page_id=1, host_id=""):
    return json.loads(
        request(method, url + f"/api/v2/hosts/?page={page_id}", headers=headers).text
    )


def get_templates(method, url, headers):
    return json.loads(
        request(method, url + "/api/v2/job_templates/", headers=headers).text
    )


def get_stdout(url, headers, job_id):
    return request("GET", url + f"/api/v2/jobs/{job_id}/stdout/", headers=headers).text


def run_template(method, url, headers, inventory_json):
    return request(
        method,
        url + "/api/v2/inventories/2/ad_hoc_commands/",
        headers=headers,
        json=inventory_json,
    ).text


def run_template_for_host(method, template_id, url, headers, data):
    return request(
        method,
        url + f"/api/v2/job_templates/{template_id}/launch/",
        headers=headers,
        data=json.dumps(data),
    )


def callback_data_dumps(json_content):
    return json.dumps(json_content)


def confirm_action():
    check_number = random.randint(0, 9999)
    check_string = f"{check_number:>04}"
    print(pyfiglet.Figlet().renderText(check_string))
    image = Image.new("RGB", (150, 100), color=("#fff"))
    draw_text = ImageDraw.Draw(image)
    draw_text.text(
        (10, 10), pyfiglet.Figlet().renderText(check_string), fill=("#1C0606")
    )
    return {"capcha_img": image, "capcha_num": str(check_string)}
