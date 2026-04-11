from decimal import Decimal

CART_SESSION_KEY = "pos_cart"


def get_cart(session):
    return session.get(CART_SESSION_KEY, {})


def save_cart(session, cart):
    session[CART_SESSION_KEY] = cart
    session.modified = True


def clear_cart(session):
    session[CART_SESSION_KEY] = {}
    session.modified = True


def add_to_cart(session, product):
    cart = get_cart(session)
    product_id = str(product.id)

    if product_id in cart:
        cart[product_id]["quantity"] += 1
    else:
        cart[product_id] = {
            "product_id": product.id,
            "name": product.name,
            "price": str(product.base_price_usd),
            "cost": str(product.cost_price_usd),
            "quantity": 1,
            "barcode": product.barcode or "",
        }

    save_cart(session, cart)


def update_quantity(session, product_id, quantity):
    cart = get_cart(session)
    product_id = str(product_id)

    if product_id in cart:
        if quantity <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id]["quantity"] = quantity
        save_cart(session, cart)


def remove_from_cart(session, product_id):
    cart = get_cart(session)
    cart.pop(str(product_id), None)
    save_cart(session, cart)


def cart_totals(cart):
    subtotal = Decimal("0")
    total_cost = Decimal("0")

    for item in cart.values():
        price = Decimal(item["price"])
        cost = Decimal(item["cost"])
        quantity = int(item["quantity"])
        subtotal += price * quantity
        total_cost += cost * quantity

    return {
        "subtotal": subtotal,
        "total_cost": total_cost,
        "total_profit": subtotal - total_cost,
    }


def increment_quantity(session, product_id):
    cart = get_cart(session)
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id]["quantity"] += 1
        save_cart(session, cart)


def decrement_quantity(session, product_id):
    cart = get_cart(session)
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id]["quantity"] -= 1

        if cart[product_id]["quantity"] <= 0:
            cart.pop(product_id, None)

        save_cart(session, cart)