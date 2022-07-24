import json
import os

import requests

from saleor_gql_loader import ETLDataLoader


def download(url: str, dest_folder: str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    filename = url.split('/')[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)

    ua = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'

    r = requests.get(url, stream=True, headers={"User-Agent": ua})
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
        return file_path
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
        return None


def insert_category(parent_id: str, name: str, url: str):
    if url is not None:
        file_path = download(url, dest_folder="categoryImages")
        if file_path is not None:
            cid = data_loader.create_category_with_image(parent_id=parent_id, name=name,
                                                         file_path=file_path)
            return cid
        else:
            ccid = data_loader.create_category(parent_id=parent_id, name=name)
            return ccid
    else:
        cccid = data_loader.create_category(parent_id=parent_id, name=name)
        return cccid


key = 'orvZ6Tr3l5JtMtW6SaMTLYX0oMuMV8'
# initialize the data_loader (optionally provide an endpoint url as second parameter)
data_loader = ETLDataLoader(key)

with open('categories.json', 'r') as jsonFile:
    data = json.load(jsonFile)

# Iterating through the json
# list
cat_to_id = {}
for category in data:
    print("-----", category.get("name"), "------")
    imageUrl = category.get("image")

    cat_to_id = insert_category(parent_id='', name=category.get("name"), url=imageUrl)

    newId = {'newId': cat_to_id}
    category.update(newId)

    subCategories = category.get("child")
    if subCategories is not None:
        for subCat in subCategories:
            print("    ", subCat.get("name"))
            subImageUrl = subCat.get("image")
            sub_cat_id = insert_category(parent_id=cat_to_id, name=subCat.get("name"), url=subImageUrl)

            newSubCatId = {'newId': sub_cat_id}
            subCat.update(newSubCatId)

            subSubCategories = subCat.get("child")
            if subSubCategories is not None:
                for subSubCat in subSubCategories:
                    print("        ", subSubCat.get("name"))
                    subSubImageUrl = subSubCat.get("image")
                    sub_sub_cat_id = insert_category(parent_id=sub_cat_id, name=subSubCat.get("name"),
                                                     url=subSubImageUrl)

                    newSubSubCatId = {'newId': sub_sub_cat_id}
                    subSubCat.update(newSubSubCatId)

with open('categories_out.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False)
