DATA_DICTIONARY = {
    "tables": {
        "customers": {
            "description": "Contains customer contact info",
            "columns": {
                "CustomerID": {
                    "description": "Unique customer identifier",
                    "synonyms": ["customer id", "customer", "client id", "client identifier"]
                },
                "CompanyName": {
                    "description": "Name of customer company",
                    "synonyms": ["company", "customer company", "business name","customer name"]
                },
                "ContactName": {
                    "description": "Name of contact person for customer",
                    "synonyms": ["contact", "contact person", "contact name"]
                },
                "ContactTitle": {
                    "description": "Job title of contact",
                    "synonyms": ["title", "contact title"]
                },
                "Address": {
                    "description": "Customer street address",
                    "synonyms": ["address", "street address"]
                },
                "City": {
                    "description": "City where customer is located",
                    "synonyms": ["city", "town"]
                },
                "Region": {
                    "description": "Region or state for customer",
                    "synonyms": ["region", "state"]
                },
                "PostalCode": {
                    "description": "Postal code of customer",
                    "synonyms": ["postal code", "zip", "zip code"]
                },
                "Country": {
                    "description": "Country of customer",
                    "synonyms": ["country", "nation"]
                },
                "Phone": {
                    "description": "Customer phone number",
                    "synonyms": ["phone", "phone number", "telephone"]
                },
                "Fax": {
                    "description": "Customer fax number",
                    "synonyms": ["fax", "fax number"]
                },
            },
        },

        "orders": {
            "description": "Order header information",
            "columns": {
                "OrderID": {
                    "description": "Unique identifier for each order",
                    "synonyms": ["order id", "order number", "order"]
                },
                "CustomerID": {
                    "description": "ID of customer placing order",
                    "synonyms": ["customer id", "who ordered"]
                },
                "EmployeeID": {
                    "description": "ID of employee handling order",
                    "synonyms": ["employee id", "handled by"]
                },
                "OrderDate": {
                    "description": "Date when order was created",
                    "synonyms": ["order date", "date"]
                },
                "RequiredDate": {
                    "description": "Date order is required",
                    "synonyms": ["required date"]
                },
                "ShippedDate": {
                    "description": "Date order was shipped",
                    "synonyms": ["shipped date"]
                },
                "Freight": {
                    "description": "Shipping cost",
                    "synonyms": ["freight", "shipping cost", "shipping charge"]
                },
                "ShipCity": {
                    "description": "City where order was shipped",
                    "synonyms": ["ship city", "shipping city"]
                },
                "ShipCountry": {
                    "description": "Country where order was shipped",
                    "synonyms": ["ship country", "shipping country"]
                },
            },
        },

        "products": {
            "description": "Product catalog and pricing",
            "columns": {
                "ProductID": {
                    "description": "Unique product identifier",
                    "synonyms": ["product id", "product number"]
                },
                "ProductName": {
                    "description": "Name of the product",
                    "synonyms": ["product", "product name", "item"]
                },
                "SupplierID": {
                    "description": "ID of supplier",
                    "synonyms": ["supplier", "who supplies"]
                },
                "CategoryID": {
                    "description": "Category classification ID",
                    "synonyms": ["category", "product category"]
                },
                "QuantityPerUnit": {
                    "description": "Quantity per unit description",
                    "synonyms": ["quantity per unit", "qty per unit"]
                },
                "UnitPrice": {
                    "description": "Price per unit",
                    "synonyms": ["unit price", "price", "cost"]
                },
                "UnitsInStock": {
                    "description": "Number of units currently in stock",
                    "synonyms": ["stock", "units in stock", "inventory"]
                },
                "UnitsOnOrder": {
                    "description": "Units currently on order",
                    "synonyms": ["units on order"]
                },
                "ReorderLevel": {
                    "description": "Level at which product should be reordered",
                    "synonyms": ["reorder level", "reorder threshold"]
                },
                "Discontinued": {
                    "description": "Whether product is discontinued",
                    "synonyms": ["discontinued", "no longer sold"]
                },
            },
        },

        "order_details": {
            "description": "Line details for orders (many-to-many orders/products)",
            "columns": {
                "OrderID": {
                    "description": "Order ID for this detail",
                    "synonyms": ["order id"]
                },
                "ProductID": {
                    "description": "Product ID for this detail",
                    "synonyms": ["product id"]
                },
                "UnitPrice": {
                    "description": "Price of product at order time",
                    "synonyms": ["unit price", "price"]
                },
                "Quantity": {
                    "description": "Quantity ordered",
                    "synonyms": ["quantity", "amount ordered"]
                },
                "Discount": {
                    "description": "Discount applied",
                    "synonyms": ["discount", "price reduction"]
                },
            },
        },

        "categories": {
            "description": "Product categories (e.g., Beverages, Seafood)",
            "columns": {
                "CategoryID": {
                    "description": "Unique category identifier",
                    "synonyms": ["category id", "category number"]
                },
                "CategoryName": {
                    "description": "Name of the product category",
                    "synonyms": ["category", "category name", "product category"]
                },
                "Description": {
                    "description": "Description of the category",
                    "synonyms": ["category description"]
                }
            }
        },

        "shippers": {
            "description": "Shipping companies that deliver orders",
            "columns": {
                "ShipperID": {
                    "description": "Unique shipper identifier",
                    "synonyms": ["shipper id", "shipping company id"]
                },
                "CompanyName": {
                    "description": "Name of the shipping company",
                    "synonyms": ["shipper", "shipping company", "carrier"]
                },
                "Phone": {
                    "description": "Shipper phone number",
                    "synonyms": ["shipper phone", "carrier phone"]
                }
            }
        },

        "suppliers": {
            "description": "Suppliers that provide products",
            "columns": {
                "SupplierID": {
                    "description": "Unique supplier identifier",
                    "synonyms": ["supplier id", "vendor id"]
                },
                "CompanyName": {
                    "description": "Supplier company name",
                    "synonyms": ["supplier", "vendor", "supplier company"]
                },
                "ContactName": {
                    "description": "Supplier contact person",
                    "synonyms": ["supplier contact", "vendor contact"]
                },
                "City": {
                    "description": "City of supplier",
                    "synonyms": ["supplier city"]
                },
                "Country": {
                    "description": "Country of supplier",
                    "synonyms": ["supplier country"]
                },
                "Phone": {
                    "description": "Supplier phone number",
                    "synonyms": ["supplier phone"]
                }
            }
        },

        "employees": {
            "description": "Company employees who manage orders",
            "columns": {
                "EmployeeID": {
                    "description": "Unique employee identifier",
                    "synonyms": ["employee id", "staff id"]
                },
                "FirstName": {
                    "description": "Employee first name",
                    "synonyms": ["first name"]
                },
                "LastName": {
                    "description": "Employee last name",
                    "synonyms": ["last name", "surname"]
                },
                "Title": {
                    "description": "Employee job title",
                    "synonyms": ["job title", "position"]
                },
                "BirthDate": {
                    "description": "Employee date of birth",
                    "synonyms": ["birthday", "date of birth"]
                },
                "HireDate": {
                    "description": "Date employee was hired",
                    "synonyms": ["hire date", "start date"]
                },
                "City": {
                    "description": "Employee city",
                    "synonyms": ["employee city"]
                },
                "Country": {
                    "description": "Employee country",
                    "synonyms": ["employee country"]
                },
                "ReportsTo": {
                    "description": "Manager employee ID",
                    "synonyms": ["manager", "reports to", "supervisor"]
                }
            }
        },

        "territories": {
            "description": "Sales territories assigned to employees",
            "columns": {
                "TerritoryID": {
                    "description": "Unique territory identifier",
                    "synonyms": ["territory id"]
                },
                "TerritoryDescription": {
                    "description": "Name/description of territory",
                    "synonyms": ["territory name", "sales territory"]
                },
                "RegionID": {
                    "description": "Region this territory belongs to",
                    "synonyms": ["region id"]
                }
            }
        },

        "employee_territories": {
            "description": "Mapping between employees and territories",
            "columns": {
                "EmployeeID": {
                    "description": "Employee assigned to territory",
                    "synonyms": ["employee id"]
                },
                "TerritoryID": {
                    "description": "Territory assigned to employee",
                    "synonyms": ["territory id"]
                }
            }
        },

        "customer_demographics": {
            "description": "Types of customer demographics",
            "columns": {
                "CustomerTypeID": {
                    "description": "Unique customer type identifier",
                    "synonyms": ["customer type id"]
                },
                "CustomerDesc": {
                    "description": "Description of customer demographic type",
                    "synonyms": ["customer type", "demographic description"]
                }
            }
        },

        "customer_customer_demo": {
            "description": "Mapping between customers and demographic types",
            "columns": {
                "CustomerID": {
                    "description": "Customer identifier",
                    "synonyms": ["customer id"]
                },
                "CustomerTypeID": {
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