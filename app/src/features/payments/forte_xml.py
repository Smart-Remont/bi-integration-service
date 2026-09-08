from xml.etree.ElementTree import Element, SubElement, tostring


def forte_create_order_xml(
    *,
    merchant: str,
    amount_tenge_kopecks: int,
    description: str,
    approve_url: str,
    cancel_url: str,
    decline_url: str,
    phone: object,
) -> str:
    root = Element("TKKPG")
    request = SubElement(root, "Request")
    SubElement(request, "Operation").text = "CreateOrder"
    SubElement(request, "Language").text = "RU"
    order = SubElement(request, "Order")
    SubElement(order, "OrderType").text = "Purchase"
    SubElement(order, "Merchant").text = merchant
    SubElement(order, "Amount").text = str(amount_tenge_kopecks)
    SubElement(order, "Currency").text = "398"
    SubElement(order, "Description").text = str(description)
    SubElement(order, "ApproveURL").text = approve_url
    SubElement(order, "CancelURL").text = cancel_url
    SubElement(order, "DeclineURL").text = decline_url
    add_params = SubElement(order, "AddParams")
    SubElement(add_params, "FA-DATA").text = str(phone or "")
    SubElement(add_params, "OrderExpirationPeriod").text = "30"
    return tostring(root, encoding="unicode")


def forte_order_status_xml(*, merchant: str, order_id: object, session_id: object) -> str:
    root = Element("TKKPG")
    request = SubElement(root, "Request")
    SubElement(request, "Operation").text = "GetOrderStatus"
    SubElement(request, "Language").text = "RU"
    order = SubElement(request, "Order")
    SubElement(order, "Merchant").text = merchant
    SubElement(order, "OrderID").text = str(order_id)
    SubElement(request, "SessionID").text = str(session_id)
    return tostring(root, encoding="unicode")
