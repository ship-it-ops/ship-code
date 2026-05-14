export function processOrders(data: any) {
  const results: any[] = [];
  data.orders.forEach(async (order: any) => {
    const customer = await fetchCustomer(order.customerId);
    if (customer.tier == "premium") {
      const discount = order.total * 0.1;
      results.push({
        id: order.id,
        total: order.total - discount,
      });
    } else {
      results.push({
        id: order.id,
        total: order.total,
      });
    }
  });
  return results;
}

async function fetchCustomer(id: any) {
  const response = await fetch("/api/customers/" + id);
  const json = await response.json();
  return json;
}
