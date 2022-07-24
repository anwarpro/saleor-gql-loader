import json
import os

import requests

from saleor_gql_loader import ETLDataLoader


def download(url: str, dest_folder: str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    filename = url.split('/')[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)
    print("downloading... ", url)

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


key = 'orvZ6Tr3l5JtMtW6SaMTLYX0oMuMV8'
# initialize the data_loader (optionally provide an endpoint url as second parameter)
data_loader = ETLDataLoader(key)

with open('productwithvariants.json', 'r') as jsonFile:
    data = json.load(jsonFile)

with open('categories_out.json', 'r') as jsonFile:
    categories = json.load(jsonFile)


def find_category(cat_id: int):
    for cat in categories:
        if cat.get("id") == cat_id:
            return cat
        if cat.get("child") is not None:
            for subCat in cat.get("child"):
                if subCat.get("id") == cat_id:
                    return subCat

                if subCat.get("child") is not None:
                    for subSubCat in subCat.get("child"):
                        if subSubCat.get("id") == cat_id:
                            return subSubCat

    return None


# Iterating through the json
# list
# 1. create or find attributes
# 2. create product type from category name (skip for now)
# 3. create product
#   3a. upload product images
#   3b. upload variants images
# 4. update product listing
# 6. create variants
# 7. Update variants listing

weight_regex = "(\d*\.?\d+)\s*(lbs?|g|gm|kg|ton)"

channels = {
    "default": "Q2hhbm5lbDox",
    "corporate": "Q2hhbm5lbDoy"
}

attributes = []

weight_attribute_id = data_loader.create_attribute(name="weight")
# # create a product type: tea
product_type_id = data_loader.create_product_type(name="Basic Type",
                                                  hasVariants=True,
                                                  productAttributes=[],
                                                  variantAttributes=[weight_attribute_id])

# product_type_id = "UHJvZHVjdFR5cGU6MjA2Nw=="
# weight_attribute_id = "QXR0cmlidXRlOjk1"

for index, products in enumerate(data):
    # if index < 200:
    #     print("skipping ", index)
    #     print("----------------------")
    #     continue
    print("importing ", index)
    print("name: ", products.get("name"))
    print("---------------------------")
    product_name = products.get("name")
    if product_name is None:
        print("skipping for product name none", index)
        print("----------------------")
        continue

    first_item = products.get("items")[0]
    ca_id = first_item.get("category_id")
    category = find_category(ca_id)

    ppdd = {
        "productType": product_type_id,
        "name": product_name
    }

    des = first_item.get("description")
    seo_title = first_item.get("seoTitle")
    seo_des = first_item.get("seoDescription")

    seo = {}
    if seo_des is not None and seo_title is not None:
        if len(seo_des) > 300:
            seo_des = seo_des[:290]
        if len(seo_title) > 70:
            seo_title = seo_title[:65]
        seo.update({
            "description": seo_des,
            "title": seo_title
        })

    if len(seo) > 0:
        ppdd.update({"seo": seo})

    if des is not None and len(des) > 0:
        jsonTemplate = "{\"time\":1656395397075,\"blocks\":[{\"type\":\"raw\",\"data\":{\"html\":\"\"}}],\"version\":\"2.24.3\"}"
        jjs = json.loads(jsonTemplate)
        bllks = jjs.get("blocks")[0].get("data")
        bllks.update({
            "html": des
        })
        y = json.dumps(jjs)
        ppdd.update({"description": y})

    if category is not None:
        ppdd.update({"category": category.get("newId")})

    product_id = data_loader.create_product(input=ppdd)

    # update product listing
    if category is not None:
        listingChannels = {
            "updateChannels": [
                {
                    "channelId": channels.get("default"),
                    "visibleInListings": True,
                    "isPublished": category is not None,
                    "isAvailableForPurchase": True,
                },
                {
                    "channelId": channels.get("corporate"),
                    "visibleInListings": True,
                    "isPublished": category is not None,
                    "isAvailableForPurchase": True,
                },
            ]
        }
    else:
        listingChannels = {
            "updateChannels": [
                {
                    "channelId": channels.get("default"),
                    "visibleInListings": True
                },
                {
                    "channelId": channels.get("corporate"),
                    "visibleInListings": True
                },
            ]
        }

    product_id = data_loader.update_product_channel_listing(product_id=product_id, input=listingChannels)
    images = []

    for product_variant in products.get("items"):
        attrs = {
            "id": weight_attribute_id,
            "values": [product_variant.get("unit")]
        }
        print("variant: ", product_variant.get("unit"))
        variant_id = data_loader.create_product_variant(product_id=product_id, attributes=[attrs])

        if variant_id is None:
            continue
        # update stock
        stocks = [
            {
                "warehouse": "V2FyZWhvdXNlOmJkODgzZDUwLWY0MTktNGU0OC1hYTBhLWM4ZTE4ZDNhNTU5MA==",
                "quantity": 10
            }
        ]

        data_loader.update_variant_stocks(variant_id=variant_id, stocks=stocks)

        images.append(product_variant.get("photos"))

        # update variant listing for price
        variantListing = [
            {
                "channelId": channels.get("default"),
                "price": product_variant.get("price"),
                "costPrice": product_variant.get("cost_price")
            },
            {
                "channelId": channels.get("corporate"),
                "price": product_variant.get("price"),
                "costPrice": product_variant.get("cost_price")
            }
        ]
        data_loader.update_variant_channel_listing(variant_id=variant_id, input=variantListing)

    all_images = []
    for img in images:
        for im in img:
            if im is not None:
                all_images.append(im)

    # download image & upload
    for imgg in all_images:
        image_path = download(imgg, "productImages")
        if image_path is not None:
            data_loader.create_product_image(product_id=product_id, file_path=image_path)

    print("-------------------------")
    # if index == 3:
    #     break

# with open('productwithvariants_out.json', 'w') as f:
#     json.dump(data, f, ensure_ascii=False)
