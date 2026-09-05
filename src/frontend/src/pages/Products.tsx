import { useEffect, useState } from "react";
import "./Products.css";

type Product = {
  id: number;
  name: string;
  description: string;
  price: number;
  inventory: number;
  category: string;
};

function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [inventory, setInventory] = useState("");
  const [category, setCategory] = useState("");

  useEffect(() => {
    fetchProducts();
  }, []);

  async function fetchProducts() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/products/"
      );

      if (!response.ok) {
        throw new Error("Failed to fetch products.");
      }

      const data = await response.json();

      setProducts(
        Array.isArray(data) ? data : []
      );
    } catch (err) {
      console.error("Products error:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Could not load products."
      );
    } finally {
      setLoading(false);
    }
  }

  function clearForm() {
    setName("");
    setDescription("");
    setPrice("");
    setInventory("");
    setCategory("");
    setEditingId(null);
  }

  function openAddForm() {
    clearForm();
    setError("");
    setShowForm(true);
  }

  function closeForm() {
    clearForm();
    setError("");
    setShowForm(false);
  }

  async function handleAddProduct(
    event: React.FormEvent
  ) {
    event.preventDefault();

    if (!name.trim() || !price || !inventory) {
      setError(
        "Product name, price and inventory are required."
      );
      return;
    }

    try {
      setSaving(true);
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/products/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name.trim(),
            description: description.trim(),
            price: Number(price),
            inventory: Number(inventory),
            category: category.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to create product."
        );
      }

      closeForm();
      await fetchProducts();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create product."
      );
    } finally {
      setSaving(false);
    }
  }

  function handleEdit(product: Product) {
    setEditingId(product.id);
    setName(product.name);
    setDescription(product.description || "");
    setPrice(String(product.price));
    setInventory(String(product.inventory));
    setCategory(product.category || "");
    setShowForm(true);
    setError("");
  }

  async function handleUpdateProduct(
    event: React.FormEvent
  ) {
    event.preventDefault();

    if (editingId === null) {
      return;
    }

    if (!name.trim() || !price || !inventory) {
      setError(
        "Product name, price and inventory are required."
      );
      return;
    }

    try {
      setSaving(true);
      setError("");

      const response = await fetch(
        `http://127.0.0.1:8000/products/${editingId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name.trim(),
            description: description.trim(),
            price: Number(price),
            inventory: Number(inventory),
            category: category.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to update product."
        );
      }

      closeForm();
      await fetchProducts();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update product."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this product?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      const response = await fetch(
        `http://127.0.0.1:8000/products/${id}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to delete product."
        );
      }

      await fetchProducts();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete product."
      );
    }
  }

  function formatMoney(value: number) {
    return `₹${Number(value || 0).toLocaleString(
      "en-IN"
    )}`;
  }

  const inStock = products.filter(
    (product) => product.inventory > 0
  ).length;

  const outOfStock = products.filter(
    (product) => product.inventory <= 0
  ).length;

  const totalInventory = products.reduce(
    (total, product) =>
      total + Number(product.inventory || 0),
    0
  );

  if (loading) {
    return (
      <div className="products-state">
        <span>03 / MUNEEM</span>

        <h1>
          Reading
          <br />
          <em>catalog.</em>
        </h1>
      </div>
    );
  }

  return (
    <div className="products-page">

      {/* =====================================================
          HERO
          ===================================================== */}

      <section className="products-hero">

        <div className="products-meta">
          <span>03 / MUNEEM</span>
          <span>PRODUCT CATALOG</span>
        </div>

        <div className="products-hero-grid">

          <div className="products-title">

            <p>COMMERCE INVENTORY</p>

            <h1>
              Know what
              <br />
              you <em>sell.</em>
            </h1>

          </div>

          <div className="products-description">

            <strong>YOUR CATALOG</strong>

            <p>
              Keep products, pricing and inventory
              in one place. MUNEEM uses this
              information to understand the commerce
              behind your revenue.
            </p>

          </div>

          <div className="products-summary">

            <div>
              <span>PRODUCTS</span>
              <strong>{products.length}</strong>
            </div>

            <div>
              <span>UNITS</span>
              <strong>{totalInventory}</strong>
            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          OVERVIEW
          ===================================================== */}

      <section className="products-overview">

        <div className="products-section-number">
          01
        </div>

        <div className="products-section-heading">

          <span>CATALOG OVERVIEW</span>

          <h2>
            Everything
            <br />
            in <em>order.</em>
          </h2>

          <p>
            {products.length} products make up your
            current catalog, with {totalInventory}
            units available.
          </p>

        </div>

        <div className="products-metrics">

          <div className="products-metric">

            <span>IN STOCK</span>

            <strong>{inStock}</strong>

            <p>
              Products currently available
              for purchase.
            </p>

          </div>

          <div className="products-metric">

            <span>OUT OF STOCK</span>

            <strong>{outOfStock}</strong>

            <p>
              Products that need inventory
              attention.
            </p>

          </div>

          <div className="products-control">

            <span>CATALOG CONTROL</span>

            <p>
              Add products or update existing
              inventory whenever your catalog changes.
            </p>

            <button
              className="products-add-button"
              onClick={
                showForm
                  ? closeForm
                  : openAddForm
              }
            >
              <span>
                {showForm
                  ? "CLOSE FORM"
                  : "ADD PRODUCT"}
              </span>

              <strong>
                {showForm ? "×" : "→"}
              </strong>
            </button>

          </div>

        </div>

      </section>


      {/* =====================================================
          ERROR
          ===================================================== */}

      {error && (
        <section className="products-notice">

          <div className="products-notice-icon">
            !
          </div>

          <div>
            <strong>Something needs attention.</strong>
            <p>{error}</p>
          </div>

        </section>
      )}


      {/* =====================================================
          PRODUCT FORM
          ===================================================== */}

      {showForm && (
        <section className="product-form-section">

          <div className="products-section-number">
            02
          </div>

          <div className="products-section-heading">

            <span>
              {editingId !== null
                ? "EDIT PRODUCT"
                : "NEW PRODUCT"}
            </span>

            <h2>
              {editingId !== null
                ? "Update your"
                : "Add a new"}
              <br />
              <em>product.</em>
            </h2>

          </div>

          <form
            className="product-form"
            onSubmit={
              editingId !== null
                ? handleUpdateProduct
                : handleAddProduct
            }
          >

            <div className="product-field">
              <label>PRODUCT NAME *</label>

              <input
                type="text"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                placeholder="Wireless Headphones"
              />
            </div>

            <div className="product-field">
              <label>CATEGORY</label>

              <input
                type="text"
                value={category}
                onChange={(event) =>
                  setCategory(event.target.value)
                }
                placeholder="Electronics"
              />
            </div>

            <div className="product-field product-field-wide">
              <label>DESCRIPTION</label>

              <textarea
                value={description}
                onChange={(event) =>
                  setDescription(event.target.value)
                }
                placeholder="Noise cancelling wireless headphones"
                rows={3}
              />
            </div>

            <div className="product-field">
              <label>PRICE *</label>

              <input
                type="number"
                min="0"
                step="0.01"
                value={price}
                onChange={(event) =>
                  setPrice(event.target.value)
                }
                placeholder="4999"
              />
            </div>

            <div className="product-field">
              <label>INVENTORY *</label>

              <input
                type="number"
                min="0"
                value={inventory}
                onChange={(event) =>
                  setInventory(event.target.value)
                }
                placeholder="25"
              />
            </div>

            <div className="product-form-actions">

              <button
                type="submit"
                disabled={saving}
                className="product-save-button"
              >
                <span>
                  {saving
                    ? "SAVING..."
                    : editingId !== null
                    ? "UPDATE PRODUCT"
                    : "SAVE PRODUCT"}
                </span>

                <strong>→</strong>
              </button>

              <button
                type="button"
                onClick={closeForm}
                className="product-cancel-button"
              >
                CANCEL
              </button>

            </div>

          </form>

        </section>
      )}


      {/* =====================================================
          CATALOG
          ===================================================== */}

      <section className="products-list-section">

        <div className="products-section-number">
          03
        </div>

        <div className="products-section-heading">

          <span>ACTIVE CATALOG</span>

          <h2>
            What you
            <br />
            <em>sell.</em>
          </h2>

        </div>

        <div className="products-table">

          <div className="products-table-header">

            <span>NO.</span>
            <span>PRODUCT</span>
            <span>CATEGORY</span>
            <span>PRICE</span>
            <span>STOCK</span>
            <span>STATUS</span>
            <span>ACTION</span>

          </div>

          {products.length === 0 ? (

            <div className="products-empty">

              <span>EMPTY CATALOG</span>

              <h3>
                Nothing here yet.
              </h3>

              <p>
                Add your first product and
                start building your catalog.
              </p>

              <button
                onClick={openAddForm}
                className="products-empty-button"
              >
                ADD FIRST PRODUCT →
              </button>

            </div>

          ) : (

            products.map((product, index) => (

              <article
                className="product-row"
                key={product.id}
              >

                <div className="product-number">
                  {String(index + 1).padStart(2, "0")}
                </div>

                <div className="product-identity">

                  <h3>{product.name}</h3>

                  <p>
                    {product.description ||
                      "No description provided."}
                  </p>

                </div>

                <div className="product-category">

                  <span>CATEGORY</span>

                  <strong>
                    {product.category ||
                      "Uncategorized"}
                  </strong>

                </div>

                <div className="product-price">

                  <span>PRICE</span>

                  <strong>
                    {formatMoney(product.price)}
                  </strong>

                </div>

                <div className="product-inventory">

                  <span>UNITS</span>

                  <strong>
                    {product.inventory}
                  </strong>

                </div>

                <div className="product-status">

                  <span
                    className={
                      product.inventory > 0
                        ? "product-status-dot available"
                        : "product-status-dot"
                    }
                  />

                  <strong>
                    {product.inventory > 0
                      ? "In stock"
                      : "Out of stock"}
                  </strong>

                </div>

                <div className="product-row-actions">

                  <button
                    onClick={() =>
                      handleEdit(product)
                    }
                  >
                    EDIT
                  </button>

                  <button
                    onClick={() =>
                      handleDelete(product.id)
                    }
                    className="delete"
                  >
                    DELETE
                  </button>

                </div>

              </article>

            ))

          )}

        </div>

      </section>


      {/* =====================================================
          BLACK MUNEEM SECTION
          ===================================================== */}

      <section className="products-insight">

        <div className="products-section-number">
          04
        </div>

        <div>

          <span className="products-insight-label">
            COMMERCE CONTEXT
          </span>

          <h2>
            The catalog
            <br />
            tells the <em>story.</em>
          </h2>

        </div>

        <div className="products-insight-copy">

          <p>
            Products are more than inventory.
            They give MUNEEM context about what
            customers buy, what is available and
            where revenue can be recovered.
          </p>

          <div className="products-principles">

            <div>
              <strong>01</strong>
              <span>PRODUCTS</span>
            </div>

            <div>
              <strong>02</strong>
              <span>INVENTORY</span>
            </div>

            <div>
              <strong>03</strong>
              <span>REVENUE</span>
            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          FOOTER
          ===================================================== */}

      <footer className="products-footer">

        <div>CATALOG</div>
        <div>INVENTORY</div>
        <div>COMMERCE</div>

        <span>
          MUNEEM · MERCHANT CONSOLE · 2026
        </span>

      </footer>

    </div>
  );
}

export default Products;