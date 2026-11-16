const productRows = document.getElementById('productRows');
const addProductRowButton = document.getElementById('addProductRow');

if (productRows && addProductRowButton) {
  const productIds = JSON.parse(productRows.dataset.productIds);
  const productNames = JSON.parse(productRows.dataset.productNames);

  function buildProductRow() {
    const row = document.createElement('div');
    row.className = 'product-row';

    const productGroup = document.createElement('div');
    productGroup.className = 'form-group';
    const productLabel = document.createElement('label');
    productLabel.textContent = 'Producto';
    const productSelect = document.createElement('select');
    productSelect.name = 'product_id';
    productSelect.required = true;
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Seleccionar';
    productSelect.appendChild(placeholder);
    productIds.forEach((id, index) => {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = productNames[index];
      productSelect.appendChild(option);
    });
    productGroup.append(productLabel, productSelect);

    const priceGroup = document.createElement('div');
    priceGroup.className = 'form-group';
    const priceLabel = document.createElement('label');
    priceLabel.textContent = 'Valor unitario';
    const priceInput = document.createElement('input');
    priceInput.type = 'number';
    priceInput.name = 'manual_price';
    priceInput.min = '1';
    priceInput.step = '0.01';
    priceInput.placeholder = 'Ingrese valor';
    priceInput.required = true;
    priceGroup.append(priceLabel, priceInput);

    const quantityGroup = document.createElement('div');
    quantityGroup.className = 'form-group';
    const quantityLabel = document.createElement('label');
    quantityLabel.textContent = 'Cantidad';
    const quantityInput = document.createElement('input');
    quantityInput.type = 'number';
    quantityInput.name = 'quantity';
    quantityInput.min = '1';
    quantityInput.value = '1';
    quantityInput.required = true;
    quantityGroup.append(quantityLabel, quantityInput);

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'remove-row-btn';
    removeButton.textContent = 'Quitar';
    row.append(productGroup, priceGroup, quantityGroup, removeButton);
    return row;
  }

  addProductRowButton.addEventListener('click', () => productRows.appendChild(buildProductRow()));
  productRows.addEventListener('click', (event) => {
    if (event.target.classList.contains('remove-row-btn') && productRows.children.length > 1) {
      event.target.closest('.product-row').remove();
    }
  });
}

