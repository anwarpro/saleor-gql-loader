from saleor_gql_loader import ETLDataLoader

key = 'orvZ6Tr3l5JtMtW6SaMTLYX0oMuMV8'
# initialize the data_loader (optionally provide an endpoint url as second parameter)
data_loader = ETLDataLoader(key)

products = [
    {
        "name": "tea a",
        "description": "description for tea a",
        "category": "green tea",
        "price": 5.5,
        "strength": "medium"
    },
    {
        "name": "tea b",
        "description": "description for tea b",
        "category": "black tea",
        "price": 10.5,
        "strength": "strong"
    },
    {
        "name": "tea c",
        "description": "description for tea c",
        "category": "green tea",
        "price": 9.5,
        "strength": "light"
    }
]

# add basic sku to products
for i, product in enumerate(products):
    product["sku"] = "{:05}-00".format(i)

# create the strength attribute
strength_attribute_id = data_loader.create_attribute(name="strength")
unique_strength = set([product['strength'] for product in products])
for strength in unique_strength:
    data_loader.create_attribute_value(strength_attribute_id, name=strength)

# create another quantity attribute used as variant:
qty_attribute_id =  data_loader.create_attribute(name="qty")
unique_qty = {"100g", "200g", "300g"}
for qty in unique_qty:
    data_loader.create_attribute_value(qty_attribute_id, name=qty)

# create a product type: tea
product_type_id = data_loader.create_product_type(name="tea",
                                                      hasVariants=True,
                                                      productAttributes=[strength_attribute_id],
                                                      variantAttributes=[qty_attribute_id])

# create categories
unique_categories = set([product['category'] for product in products])

cat_to_id = {}
for category in unique_categories:
    cat_to_id[category] = data_loader.create_category(name=category)

print(cat_to_id)

# create products and store id
for i, product in enumerate(products):
    if i == 2:
        break

    product_id = data_loader.create_product(product_type_id,
                                                name=product["name"],
                                                category=cat_to_id[product["category"]])
    products[i]["id"] = product_id
