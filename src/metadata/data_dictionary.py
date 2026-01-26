DATA_DICTIONARY = {
    "tables": {
        "customers": {
            "description": "Contains customer contact info",
            "columns": {
                "customer_id": {
                    "description": "Unique customer identifier",
                    "synonyms": ["customer id", "customer", "client id", "client identifier"]
                },
                "company_name": {
                    "description": "Name of customer company",
                    "synonyms": ["company", "customer company", "business name"]
                },
                "contact_name": {
                    "description": "Name of contact person for customer",
                    "synonyms": ["contact", "contact person", "contact name"]
                },
                "contact_title": {
                    "description": "Job title of contact",
                    "synonyms": ["title", "contact title"]
                },
                "address": {
                    "description": "Customer street address",
                    "synonyms": ["address", "street address"]
                },
                "city": {
                    "description": "City where customer is located",
                    "synonyms": ["city", "town"]
                },
                "region": {
                    "description": "Region or state for customer",
                    "synonyms": ["region", "state"]
                },
                "postal_code": {
                    "description": "Postal code of customer",
                    "synonyms": ["postal code", "zip", "zip code"]
                },
                "country": {
                    "description": "Country of customer",
                    "synonyms": ["country", "nation"]
                },
                "phone": {
                    "description": "Customer phone number",
                    "synonyms": ["phone", "phone number", "telephone"]
                },
                "fax": {
                    "description": "Customer fax number",
                    "synonyms": ["fax", "fax number"]
                },
            },
        },

        "orders": {
            "description": "Order header information",
            "columns": {
                "order_id": {
                    "description": "Unique identifier for each order",
                    "synonyms": ["order id", "order number", "order"]
                },
                "customer_id": {
                    "description": "ID of customer placing order",
                    "synonyms": ["customer id", "who ordered"]
                },
                "employee_id": {
                    "description": "ID of employee handling order",
                    "synonyms": ["employee id", "handled by"]
                },
                "order_date": {
                    "description": "Date when order was created",
                    "synonyms": ["order date", "date"]
                },
                "required_date": {
                    "description": "Date order is required",
                    "synonyms": ["required date"]
                },
                "shipped_date": {
                    "description": "Date order was shipped",
                    "synonyms": ["shipped date"]
                },
                "freight": {
                    "description": "Shipping cost",
                    "synonyms": ["freight", "shipping cost", "shipping charge"]
                },
                "ship_city": {
                    "description": "City where order was shipped",
                    "synonyms": ["ship city", "shipping city"]
                },
                "ship_country": {
                    "description": "Country where order was shipped",
                    "synonyms": ["ship country", "shipping country"]
                },
            },
        },

        "products": {
            "description": "Product catalog and pricing",
            "columns": {
                "product_id": {
                    "description": "Unique product identifier",
                    "synonyms": ["product id", "product number"]
                },
                "product_name": {
                    "description": "Name of the product",
                    "synonyms": ["product", "product name", "item"]
                },
                "supplier_id": {
                    "description": "ID of supplier",
                    "synonyms": ["supplier", "who supplies"]
                },
                "category_id": {
                    "description": "Category classification ID",
                    "synonyms": ["category", "product category"]
                },
                "quantity_per_unit": {
                    "description": "Quantity per unit description",
                    "synonyms": ["quantity per unit", "qty per unit"]
                },
                "unit_price": {
                    "description": "Price per unit",
                    "synonyms": ["unit price", "price", "cost"]
                },
                "units_in_stock": {
                    "description": "Number of units currently in stock",
                    "synonyms": ["stock", "units in stock", "inventory"]
                },
                "units_on_order": {
                    "description": "Units currently on order",
                    "synonyms": ["units on order"]
                },
                "reorder_level": {
                    "description": "Level at which product should be reordered",
                    "synonyms": ["reorder level", "reorder threshold"]
                },
                "discontinued": {
                    "description": "Whether product is discontinued",
                    "synonyms": ["discontinued", "no longer sold"]
                },
            },
        },

        "order_details": {
            "description": "Line details for orders (many-to-many orders/products)",
            "columns": {
                "order_id": {
                    "description": "Order ID for this detail",
                    "synonyms": ["order id"]
                },
                "product_id": {
                    "description": "Product ID for this detail",
                    "synonyms": ["product id"]
                },
                "unit_price": {
                    "description": "Price of product at order time",
                    "synonyms": ["unit price", "price"]
                },
                "quantity": {
                    "description": "Quantity ordered",
                    "synonyms": ["quantity", "amount ordered"]
                },
                "discount": {
                    "description": "Discount applied",
                    "synonyms": ["discount", "price reduction"]
                },
            },
        },

        "categories": {
            "description": "Product categories (e.g., Beverages, Seafood)",
            "columns": {
                "category_id": {
                    "description": "Unique category identifier",
                    "synonyms": ["category id", "category number"]
                },
                "category_name": {
                    "description": "Name of the product category",
                    "synonyms": ["category", "category name", "product category"]
                },
                "description": {
                    "description": "Description of the category",
                    "synonyms": ["category description"]
                }
            }
        },

        "shippers": {
            "description": "Shipping companies that deliver orders",
            "columns": {
                "shipper_id": {
                    "description": "Unique shipper identifier",
                    "synonyms": ["shipper id", "shipping company id"]
                },
                "company_name": {
                    "description": "Name of the shipping company",
                    "synonyms": ["shipper", "shipping company", "carrier"]
                },
                "phone": {
                    "description": "Shipper phone number",
                    "synonyms": ["shipper phone", "carrier phone"]
                }
            }
        },

        "suppliers": {
            "description": "Suppliers that provide products",
            "columns": {
                "supplier_id": {
                    "description": "Unique supplier identifier",
                    "synonyms": ["supplier id", "vendor id"]
                },
                "company_name": {
                    "description": "Supplier company name",
                    "synonyms": ["supplier", "vendor", "supplier company"]
                },
                "contact_name": {
                    "description": "Supplier contact person",
                    "synonyms": ["supplier contact", "vendor contact"]
                },
                "city": {
                    "description": "City of supplier",
                    "synonyms": ["supplier city"]
                },
                "country": {
                    "description": "Country of supplier",
                    "synonyms": ["supplier country"]
                },
                "phone": {
                    "description": "Supplier phone number",
                    "synonyms": ["supplier phone"]
                }
            }
        },

        "employees": {
            "description": "Company employees who manage orders",
            "columns": {
                "employee_id": {
                    "description": "Unique employee identifier",
                    "synonyms": ["employee id", "staff id"]
                },
                "first_name": {
                    "description": "Employee first name",
                    "synonyms": ["first name"]
                },
                "last_name": {
                    "description": "Employee last name",
                    "synonyms": ["last name", "surname"]
                },
                "title": {
                    "description": "Employee job title",
                    "synonyms": ["job title", "position"]
                },
                "birth_date": {
                    "description": "Employee date of birth",
                    "synonyms": ["birthday", "date of birth"]
                },
                "hire_date": {
                    "description": "Date employee was hired",
                    "synonyms": ["hire date", "start date"]
                },
                "city": {
                    "description": "Employee city",
                    "synonyms": ["employee city"]
                },
                "country": {
                    "description": "Employee country",
                    "synonyms": ["employee country"]
                },
                "reports_to": {
                    "description": "Manager employee ID",
                    "synonyms": ["manager", "reports to", "supervisor"]
                }
            }
        },

        "territories": {
            "description": "Sales territories assigned to employees",
            "columns": {
                "territory_id": {
                    "description": "Unique territory identifier",
                    "synonyms": ["territory id"]
                },
                "territory_description": {
                    "description": "Name/description of territory",
                    "synonyms": ["territory name", "sales territory"]
                },
                "region_id": {
                    "description": "Region this territory belongs to",
                    "synonyms": ["region id"]
                }
            }
        },

        "employee_territories": {
            "description": "Mapping between employees and territories",
            "columns": {
                "employee_id": {
                    "description": "Employee assigned to territory",
                    "synonyms": ["employee id"]
                },
                "territory_id": {
                    "description": "Territory assigned to employee",
                    "synonyms": ["territory id"]
                }
            }
        },

        "customer_demographics": {
            "description": "Types of customer demographics",
            "columns": {
                "customer_type_id": {
                    "description": "Unique customer type identifier",
                    "synonyms": ["customer type id"]
                },
                "customer_desc": {
                    "description": "Description of customer demographic type",
                    "synonyms": ["customer type", "demographic description"]
                }
            }
        },

        "customer_customer_demo": {
            "description": "Mapping between customers and demographic types",
            "columns": {
                "customer_id": {
                    "description": "Customer identifier",
                    "synonyms": ["customer id"]
                },
                "customer_type_id": {
                    "description": "Customer demographic type identifier",
                    "synonyms": ["customer type id"]
                }
            }
        },

    }
}


DICT_PROMPT=f"""
You have the following data dictionary:

{DATA_DICTIONARY}

If user refers to a synonym, map to the real column name.
Always generate SQL using actual column names.
"""