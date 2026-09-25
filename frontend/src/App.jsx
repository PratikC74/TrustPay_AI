import { useEffect, useState } from "react";


const summaryCardStyle = {
  background: "#ffffff",
  border: "1px solid #e2e8f0",
  padding: "14px 16px",
  borderRadius: "12px",
  boxShadow: "none",
};



const buttonStyle = {
  padding: "10px 14px",
  border: "1px solid #e2e8f0",
  borderRadius: "9px",
  cursor: "pointer",
  fontWeight: "600",
  background: "#ffffff",
  color: "#0f172a",
};

const inputStyle = {
  padding: "10px 12px",
  border: "1px solid #e2e8f0",
  borderRadius: "9px",
  background: "#ffffff",
  color: "#0f172a",
};

function App() {
  // ==================================================
  // Authentication
  // ==================================================
  const [loggedIn, setLoggedIn] = useState(
    Boolean(localStorage.getItem("trustpay_token"))
  );

  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
  });

  const [loginError, setLoginError] = useState("");

  const [currentUser, setCurrentUser] = useState(() => {
    const savedUser = localStorage.getItem("trustpay_user");

    if (!savedUser) {
      return null;
    }

    try {
      return JSON.parse(savedUser);
    } catch {
      return null;
    }
  });

  const isAdmin = currentUser?.role === "admin";

  // ==================================================
  // Transactions
  // ==================================================
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ==================================================
  // Audit Logs
  // ==================================================
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  // ==================================================
  // Filters
  // ==================================================
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");

  // ==================================================
  // Payment Form
  // ==================================================
  const [form, setForm] = useState({
    user_id: 1,
    amount: "",
    payment_method: "UPI",
    transaction_reference: "",
  });

  // ==================================================
  // Login
  // ==================================================
  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      setLoginError("");

      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: loginForm.email.trim(),
          password: loginForm.password,
        }),
      });

      const responseText = await response.text();

      let data = {};

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          throw new Error(
            `Backend returned an invalid response (${response.status})`
          );
        }
      }

      if (!response.ok) {
        throw new Error(
          data.detail || `Login failed with status ${response.status}`
        );
      }

      if (!data.access_token) {
        throw new Error(
          "Login response did not contain an access token"
        );
      }

      localStorage.setItem(
        "trustpay_token",
        data.access_token
      );

      const userData = {
        user_id: data.user_id,
        name: data.name,
        email: data.email,
        role: data.role,
      };

      localStorage.setItem(
        "trustpay_user",
        JSON.stringify(userData)
      );

      setCurrentUser(userData);
      setLoggedIn(true);

      setLoginForm({
        email: "",
        password: "",
      });
    } catch (err) {
      setLoginError(err.message || "Login failed");
    }
  };

  // ==================================================
  // Logout
  // ==================================================
  const handleLogout = () => {
    localStorage.removeItem("trustpay_token");
    localStorage.removeItem("trustpay_user");

    setLoggedIn(false);
    setCurrentUser(null);
    setTransactions([]);
    setAuditLogs([]);
    setError("");
  };

  // ==================================================
  // Fetch Transactions
  // ==================================================
  const fetchTransactions = async () => {
    if (!loggedIn) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const params = new URLSearchParams();

      if (search.trim()) {
        params.append("search", search.trim());
      }

      if (statusFilter) {
        params.append("status", statusFilter);
      }

      if (riskFilter) {
        params.append("risk_level", riskFilter);
      }

      const queryString = params.toString();

      const url = queryString
        ? `/api/transactions/?${queryString}`
        : "/api/transactions/";

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${
            localStorage.getItem("trustpay_token") || ""
          }`,
        },
      });

      const responseText = await response.text();

      let data = [];

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          throw new Error(
            `Invalid transaction response (${response.status})`
          );
        }
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to fetch transactions"
        );
      }

      setTransactions(data);
    } catch (err) {
      setError(
        err.message || "Failed to fetch transactions"
      );
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Fetch Audit Logs
  // ==================================================
  const fetchAuditLogs = async () => {
    if (!loggedIn || !isAdmin) {
      return;
    }

    try {
      setAuditLoading(true);

      const response = await fetch("/api/audit-logs/", {
        headers: {
          Authorization: `Bearer ${
            localStorage.getItem("trustpay_token") || ""
          }`,
        },
      });

      const responseText = await response.text();

      let data = [];

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          throw new Error(
            `Invalid audit log response (${response.status})`
          );
        }
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to fetch audit logs"
        );
      }

      setAuditLogs(data);
    } catch (err) {
      setError(
        err.message || "Failed to fetch audit logs"
      );
    } finally {
      setAuditLoading(false);
    }
  };

  // ==================================================
  // Load data after login
  // ==================================================
  useEffect(() => {
    if (loggedIn) {
      fetchTransactions();
      fetchAuditLogs();
    }
  }, [loggedIn, isAdmin]);

  // ==================================================
  // Handle Payment Form Changes
  // ==================================================
  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  // ==================================================
  // Create Transaction
  // ==================================================
  const createTransaction = async (e) => {
    e.preventDefault();

    try {
      setError("");

      const response = await fetch("/api/transactions/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${
            localStorage.getItem("trustpay_token") || ""
          }`,
        },
        body: JSON.stringify({
          user_id: Number(form.user_id),
          amount: Number(form.amount),
          currency: "INR",
          payment_method: form.payment_method,
          status: "pending",
          transaction_reference:
            form.transaction_reference.trim(),
        }),
      });

      const responseText = await response.text();

      let data = {};

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          throw new Error(
            `Invalid server response (${response.status})`
          );
        }
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Transaction creation failed"
        );
      }

      setForm({
        user_id: 1,
        amount: "",
        payment_method: "UPI",
        transaction_reference: "",
      });

      await fetchTransactions();
      await fetchAuditLogs();
    } catch (err) {
      setError(
        err.message || "Transaction creation failed"
      );
    }
  };

  // ==================================================
  // Clear Filters
  // ==================================================
  const clearFilters = async () => {
    setSearch("");
    setStatusFilter("");
    setRiskFilter("");

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "/api/transactions/",
        {
          headers: {
            Authorization: `Bearer ${
              localStorage.getItem("trustpay_token") || ""
            }`,
          },
        }
      );

      const responseText = await response.text();

      let data = [];

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          throw new Error(
            `Invalid server response (${response.status})`
          );
        }
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to fetch transactions"
        );
      }

      setTransactions(data);
    } catch (err) {
      setError(
        err.message || "Failed to fetch transactions"
      );
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Update Transaction Status
  // ==================================================
  const updateStatus = async (
    transactionId,
    status
  ) => {
    if (!isAdmin) {
      setError(
        "Admin access required for this action."
      );
      return;
    }

    const transaction = transactions.find(
      (item) => item.id === transactionId
    );

    const riskLevel =
      transaction?.risk_assessment?.risk_level?.toLowerCase();

    if (status === "approved" && riskLevel !== "low") {
      setError(
        `${
          riskLevel?.toUpperCase() || "UNKNOWN"
        }-risk transaction cannot be approved.`
      );
      return;
    }

    if (
      status === "review" &&
      riskLevel === "high"
    ) {
      setError(
        "High-risk transactions should be blocked."
      );
      return;
    }

    if (
      status === "blocked" &&
      riskLevel === "low"
    ) {
      setError(
        "Low-risk transactions are recommended for approval."
      );
      return;
    }

    try {
      setError("");

      const response = await fetch(
        `/api/transactions/${transactionId}/status`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${
              localStorage.getItem("trustpay_token") || ""
            }`,
          },
          body: JSON.stringify({
            status,
          }),
        }
      );

      const responseText = await response.text();

      let data = {};

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          throw new Error(
            `Invalid server response (${response.status})`
          );
        }
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to update transaction status"
        );
      }

      await fetchTransactions();
      await fetchAuditLogs();
    } catch (err) {
      setError(
        err.message ||
          "Failed to update transaction status"
      );
    }
  };

  // ==================================================
  // Execute Payment
  // ==================================================
  const executePayment = async (transactionId) => {
    if (!isAdmin) {
      setError(
        "Admin access required for payment execution."
      );
      return;
    }

    try {
      setError("");

      const response = await fetch(
        `/api/transactions/${transactionId}/execute`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${
              localStorage.getItem("trustpay_token") || ""
            }`,
          },
        }
      );

      const responseText = await response.text();

      let data = {};

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          throw new Error(
            `Invalid server response (${response.status})`
          );
        }
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Payment execution failed"
        );
      }

      await fetchTransactions();
      await fetchAuditLogs();

      alert(
        `Payment executed successfully!\nTransaction #${transactionId}`
      );
    } catch (err) {
      setError(
        err.message || "Payment execution failed"
      );
    }
  };

  // ==================================================
  // AI Recommended Decision
  // ==================================================
  const getRecommendedDecision = (transaction) => {
    const riskLevel =
      transaction.risk_assessment?.risk_level?.toLowerCase();

    if (riskLevel === "low") {
      return "APPROVED";
    }

    if (riskLevel === "medium") {
      return "REVIEW";
    }

    if (riskLevel === "high") {
      return "BLOCKED";
    }

    return "PENDING";
  };

  // ==================================================
  // Dashboard Calculations
  // ==================================================
  const totalTransactions = transactions.length;

  const totalAmount = transactions.reduce(
    (sum, transaction) =>
      sum + Number(transaction.amount),
    0
  );

  const suspiciousTransactions = transactions.filter(
    (transaction) =>
      transaction.risk_assessment?.is_suspicious === true
  ).length;

  const reviewTransactions = transactions.filter(
    (transaction) =>
      transaction.risk_assessment?.risk_level?.toLowerCase() ===
      "medium"
  ).length;

  const completedTransactions = transactions.filter(
    (transaction) =>
      transaction.status === "completed"
  ).length;

  const lowRiskTransactions = transactions.filter(
    (transaction) =>
      transaction.risk_assessment?.risk_level?.toLowerCase() ===
      "low"
  ).length;

  const mediumRiskTransactions = transactions.filter(
    (transaction) =>
      transaction.risk_assessment?.risk_level?.toLowerCase() ===
      "medium"
  ).length;

  const highRiskTransactions = transactions.filter(
    (transaction) =>
      transaction.risk_assessment?.risk_level?.toLowerCase() ===
      "high"
  ).length;

  // ==================================================
  // LOGIN SCREEN
  // ==================================================
  if (!loggedIn) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          background: "#f8fafc",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <form
          onSubmit={handleLogin}
          style={{
            background: "#ffffff",
            padding: "28px 24px",
            borderRadius: "18px",
            width: "360px",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 12px rgba(15, 23, 42, 0.03)",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "2rem", letterSpacing: "-0.06em" }}>TrustPay AI</h1>

          <p style={{ margin: "8px 0 18px", color: "#64748b", fontSize: "0.95rem" }}>Login to Payment Risk Dashboard</p>

          {loginError && (
            <div
              style={{
                background: "#fee2e2",
                color: "#991b1b",
                padding: "10px",
                borderRadius: "10px",
                marginBottom: "15px",
                fontWeight: "600",
                border: "1px solid rgba(153, 27, 27, 0.08)",
              }}
            >
              {loginError}
            </div>
          )}

          <input
            type="email"
            placeholder="Email"
            value={loginForm.email}
            onChange={(e) =>
              setLoginForm({
                ...loginForm,
                email: e.target.value,
              })
            }
            required
            style={{
              width: "100%",
              padding: "11px 12px",
              marginBottom: "12px",
              boxSizing: "border-box",
              border: "1px solid #e2e8f0",
              borderRadius: "9px",
              background: "#ffffff",
            }}
          />

          <input
            type="password"
            placeholder="Password"
            value={loginForm.password}
            onChange={(e) =>
              setLoginForm({
                ...loginForm,
                password: e.target.value,
              })
            }
            required
            style={{
              width: "100%",
              padding: "11px 12px",
              marginBottom: "15px",
              boxSizing: "border-box",
              border: "1px solid #e2e8f0",
              borderRadius: "9px",
              background: "#ffffff",
            }}
          />

          <button
            type="submit"
            style={{
              width: "100%",
              padding: "12px 14px",
              border: "none",
              borderRadius: "10px",
              background: "#2563eb",
              color: "white",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            Login
          </button>
        </form>
      </div>
    );
  }

  // ==================================================
  // DASHBOARD
  // ==================================================
  return (
    <div
      className="dashboard-page"
      style={{
        minHeight: "100vh",
        padding: "28px",
        fontFamily: "Arial, sans-serif",
        background: "#f8fafc",
      }}
    >
      {/* Header */}
      <div
        className="dashboard-header"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "18px",
          paddingBottom: "12px",
          borderBottom: "1px solid #e2e8f0",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "28px", fontWeight: 700, letterSpacing: "-0.03em" }}>TrustPay AI</h1>

          <p style={{ margin: "5px 0 0", color: "#64748b", fontSize: "14px" }}>
            AI-Powered Payment Risk & Decision Dashboard
          </p>

          {currentUser && (
            <p style={{ margin: "5px 0 0", color: "#64748b", fontSize: "13px" }}>
              Logged in as:{" "}
              <strong>{currentUser.name}</strong>{" "}
              ({currentUser.role})
            </p>
          )}
        </div>

        <button
          onClick={handleLogout}
          style={{
            ...buttonStyle,
            background: "#ffffff",
            color: "#475569",
            borderColor: "#e2e8f0",
          }}
        >
          Logout
        </button>
      </div>

      {/* Summary Cards */}
      <div
        className="kpi-grid"
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(5, minmax(160px, 1fr))",
          gap: "14px",
          marginTop: "18px",
          marginBottom: "20px",
        }}
      >
        <div className="kpi-card" style={summaryCardStyle}>
          <h3>Total Transactions</h3>
          <h2>{totalTransactions}</h2>
        </div>

        <div className="kpi-card" style={summaryCardStyle}>
          <h3>Total Amount</h3>
          <h2>
            ₹{totalAmount.toLocaleString("en-IN")}
          </h2>
        </div>

        <div className="kpi-card" style={summaryCardStyle}>
          <h3>Suspicious</h3>
          <h2>{suspiciousTransactions}</h2>
        </div>

        <div className="kpi-card" style={summaryCardStyle}>
          <h3>Need Review</h3>
          <h2>{reviewTransactions}</h2>
        </div>

        <div className="kpi-card" style={summaryCardStyle}>
          <h3>Completed</h3>
          <h2>{completedTransactions}</h2>
        </div>
      </div>

      {/* Risk Summary */}
      <div
        className="risk-panel"
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          padding: "16px 18px",
          borderRadius: "12px",
          marginBottom: "20px",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "19px", fontWeight: 650, letterSpacing: "-0.02em" }}>Risk Summary</h2>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(3, minmax(160px, 1fr))",
            gap: "12px",
            marginTop: "12px",
          }}
        >
          <div className="risk-card risk-low-card" style={summaryCardStyle}>
            <h3>LOW Risk</h3>
            <h2>{lowRiskTransactions}</h2>
          </div>

          <div className="risk-card risk-medium-card" style={summaryCardStyle}>
            <h3>MEDIUM Risk</h3>
            <h2>{mediumRiskTransactions}</h2>
          </div>

          <div className="risk-card risk-high-card" style={summaryCardStyle}>
            <h3>HIGH Risk</h3>
            <h2>{highRiskTransactions}</h2>
          </div>
        </div>
      </div>

      {/* Create Payment */}
      <form
        className="payment-panel"
        onSubmit={createTransaction}
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          padding: "16px 18px",
          borderRadius: "12px",
          marginBottom: "18px",
        }}
      >
        <h2 style={{ margin: "0 0 12px", fontSize: "19px", fontWeight: 650, letterSpacing: "-0.02em" }}>Create Payment</h2>

        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
          }}
        >
          <input
            type="number"
            name="amount"
            placeholder="Amount"
            value={form.amount}
            onChange={handleChange}
            required
            min="1"
            style={inputStyle}
          />

          <select
            name="payment_method"
            value={form.payment_method}
            onChange={handleChange}
            style={inputStyle}
          >
            <option value="UPI">UPI</option>
            <option value="Card">Card</option>
            <option value="Wallet">Wallet</option>
          </select>

          <input
            type="text"
            name="transaction_reference"
            placeholder="Transaction Reference"
            value={form.transaction_reference}
            onChange={handleChange}
            required
            style={{
              ...inputStyle,
              minWidth: "240px",
            }}
          />

          <button
            type="submit"
            style={{
              ...buttonStyle,
              background: "#2563eb",
              color: "white",
              borderColor: "#1d4ed8",
            }}
          >
            Create Payment
          </button>
        </div>
      </form>

      {/* Filters */}
      <div
        className="filter-panel"
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          padding: "14px 18px",
          borderRadius: "12px",
          marginBottom: "18px",
        }}
      >
        <h2 style={{ margin: "0 0 10px", fontSize: "19px", fontWeight: 650, letterSpacing: "-0.02em" }}>Transaction Filters</h2>

        <div
          style={{
            display: "flex",
            gap: "10px",
            flexWrap: "wrap",
          }}
        >
          <input
            type="text"
            placeholder="Search reference or payment method"
            value={search}
            onChange={(e) =>
              setSearch(e.target.value)
            }
            style={{
              ...inputStyle,
              minWidth: "300px",
            }}
          />

          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value)
            }
            style={inputStyle}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="review">Review</option>
            <option value="blocked">Blocked</option>
            <option value="completed">Completed</option>
          </select>

          <select
            value={riskFilter}
            onChange={(e) =>
              setRiskFilter(e.target.value)
            }
            style={inputStyle}
          >
            <option value="">All Risk Levels</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>

          <button
            type="button"
            onClick={fetchTransactions}
            style={{
              ...buttonStyle,
              background: "#2563eb",
              color: "white",
              borderColor: "#1d4ed8",
            }}
          >
            Apply Filters
          </button>

          <button
            type="button"
            onClick={clearFilters}
            style={{
              ...buttonStyle,
              background: "#ffffff",
              color: "#475569",
              borderColor: "#e2e8f0",
            }}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Refresh */}
      <div
        className="refresh-actions"
        style={{
          display: "flex",
          gap: "10px",
          flexWrap: "wrap",
          marginBottom: "20px",
        }}
      >
        <button
          onClick={fetchTransactions}
          style={{
            ...buttonStyle,
            background: "#ffffff",
            borderColor: "#e2e8f0",
            color: "white",
            color: "#475569",
          }}
        >
          {loading
            ? "Refreshing..."
            : "Refresh Transactions"}
        </button>

        {isAdmin && (
          <button
            onClick={fetchAuditLogs}
            style={{
              ...buttonStyle,
              background: "#ffffff",
              color: "#475569",
            }}
          >
            {auditLoading
              ? "Refreshing Logs..."
              : "Refresh Audit Logs"}
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            background: "#fee2e2",
            color: "#991b1b",
            padding: "12px 16px",
            borderRadius: "9px",
            marginBottom: "20px",
            fontWeight: "600",
            border: "1px solid rgba(153, 27, 27, 0.08)",
          }}
        >
          {error}
        </div>
      )}

      {/* Transaction List */}
      <div
        className="transaction-list"
        style={{
          display: "grid",
          gap: "20px",
          marginTop: "20px",
        }}
      >
        {transactions.length === 0 && !loading && (
          <div style={summaryCardStyle}>
            <p>No transactions found.</p>
          </div>
        )}

        {transactions.map((transaction) => {
          const riskLevel =
            transaction.risk_assessment?.risk_level?.toLowerCase();

          const recommendedDecision =
            getRecommendedDecision(transaction);

          const isLowRisk = riskLevel === "low";
          const isHighRisk = riskLevel === "high";

          const isCompleted =
            transaction.status === "completed";

          const canApprove =
            isAdmin &&
            isLowRisk &&
            !isCompleted;

          const canReview =
            isAdmin &&
            !isHighRisk &&
            !isCompleted;

          const canBlock =
            isAdmin &&
            !isLowRisk &&
            !isCompleted;

          const canExecute =
            isAdmin &&
            isLowRisk &&
            transaction.status === "approved";

          return (
            <div
              className="transaction-card"
              key={transaction.id}
              style={{
                background: "#ffffff",
                border: "1px solid #e2e8f0",
                padding: "16px 18px",
                borderRadius: "12px",
              }}
            >
              <h2 style={{ margin: 0, fontSize: "19px", fontWeight: 650, letterSpacing: "-0.02em" }}>
                Transaction #{transaction.id}
              </h2>

              <p>
                <strong>Amount:</strong> ₹
                {Number(
                  transaction.amount
                ).toLocaleString("en-IN")}
              </p>

              <p>
                <strong>Payment Method:</strong>{" "}
                {transaction.payment_method}
              </p>

              <p>
                <strong>Reference:</strong>{" "}
                {transaction.transaction_reference}
              </p>

              {/* Status */}
              <p>
                <strong>Status:</strong>{" "}
                <span
                  style={{
                    padding: "5px 10px",
                    borderRadius: "20px",
                    fontWeight: "600",
                    background:
                      transaction.status === "approved"
                        ? "#d1fae5"
                        : transaction.status === "review"
                        ? "#fef3c7"
                        : transaction.status === "blocked"
                        ? "#fee2e2"
                        : transaction.status === "completed"
                        ? "#dbeafe"
                        : "#e2e8f0",
                    color:
                      transaction.status === "approved"
                        ? "#065f46"
                        : transaction.status === "review"
                        ? "#92400e"
                        : transaction.status === "blocked"
                        ? "#991b1b"
                        : transaction.status === "completed"
                        ? "#1e40af"
                        : "#64748b",
                  }}
                >
                  {transaction.status.toUpperCase()}
                </span>
              </p>

              {/* AI Risk Assessment */}
              {transaction.risk_assessment && (
                <div
                  style={{
                    marginTop: "16px",
                    padding: "16px",
                    background: "#f8fafc",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <h3 style={{ margin: "0 0 10px", fontSize: "16px", fontWeight: 650 }}>AI Risk Assessment</h3>

                  <p>
                    <strong>Risk Score:</strong>{" "}
                    {transaction.risk_assessment.risk_score}
                  </p>

                  <p>
                    <strong>Risk Level:</strong>{" "}
                    <span
                      style={{
                        padding: "5px 10px",
                        borderRadius: "20px",
                        fontWeight: "600",
                        background:
                          riskLevel === "low"
                            ? "#d1fae5"
                            : riskLevel === "medium"
                            ? "#fef3c7"
                            : riskLevel === "high"
                            ? "#fee2e2"
                            : "#e2e8f0",
                        color:
                          riskLevel === "low"
                            ? "#065f46"
                            : riskLevel === "medium"
                            ? "#92400e"
                            : riskLevel === "high"
                            ? "#991b1b"
                            : "#64748b",
                      }}
                    >
                      {riskLevel
                        ? riskLevel.toUpperCase()
                        : "UNKNOWN"}
                    </span>
                  </p>

                  <p>
                    <strong>
                      AI Recommended Decision:
                    </strong>{" "}
                    <span
                      style={{
                        padding: "6px 12px",
                        borderRadius: "20px",
                        fontWeight: "600",
                        background:
                          recommendedDecision === "APPROVED"
                            ? "#d1fae5"
                            : recommendedDecision === "REVIEW"
                            ? "#fef3c7"
                            : recommendedDecision === "BLOCKED"
                            ? "#fee2e2"
                            : "#e2e8f0",
                        color:
                          recommendedDecision === "APPROVED"
                            ? "#065f46"
                            : recommendedDecision === "REVIEW"
                            ? "#92400e"
                            : recommendedDecision === "BLOCKED"
                            ? "#991b1b"
                            : "#64748b",
                      }}
                    >
                      {recommendedDecision}
                    </span>
                  </p>

                  <p>
                    <strong>Suspicious:</strong>{" "}
                    {transaction.risk_assessment
                      .is_suspicious
                      ? "Yes"
                      : "No"}
                  </p>

                  <p>
                    <strong>Reason:</strong>{" "}
                    {transaction.risk_assessment.reason}
                  </p>

                  <p>
                    <strong>
                      AI Recommendation:
                    </strong>{" "}
                    {
                      transaction.risk_assessment
                        .ai_recommendation
                    }
                  </p>
                </div>
              )}

              {/* Payment Actions */}
              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  marginTop: "20px",
                  flexWrap: "wrap",
                }}
              >
                {/* Approve */}
                <button
                  onClick={() =>
                    updateStatus(
                      transaction.id,
                      "approved"
                    )
                  }
                  disabled={!canApprove}
                  style={{
                    ...buttonStyle,
                    background: canApprove
                      ? "#16a34a"
                      : "#9ca3af",
                    color: "white",
                    cursor: canApprove
                      ? "pointer"
                      : "not-allowed",
                  }}
                >
                  {isCompleted
                    ? "Completed"
                    : canApprove
                    ? "Approve"
                    : "Approve Disabled"}
                </button>

                {/* Review */}
                <button
                  onClick={() =>
                    updateStatus(
                      transaction.id,
                      "review"
                    )
                  }
                  disabled={!canReview}
                  style={{
                    ...buttonStyle,
                    background: canReview
                      ? "#d97706"
                      : "#9ca3af",
                    color: "white",
                    cursor: canReview
                      ? "pointer"
                      : "not-allowed",
                  }}
                >
                  {isAdmin
                    ? "Review"
                    : "Review Disabled"}
                </button>

                {/* Block */}
                <button
                  onClick={() =>
                    updateStatus(
                      transaction.id,
                      "blocked"
                    )
                  }
                  disabled={!canBlock}
                  style={{
                    ...buttonStyle,
                    background: canBlock
                      ? "#dc2626"
                      : "#9ca3af",
                    color: "white",
                    cursor: canBlock
                      ? "pointer"
                      : "not-allowed",
                  }}
                >
                  {isAdmin
                    ? "Block"
                    : "Block Disabled"}
                </button>

                {/* Execute */}
                {canExecute && (
                  <button
                    onClick={() =>
                      executePayment(transaction.id)
                    }
                    style={{
                      ...buttonStyle,
                      background: "#2563eb",
                      color: "white",
                    }}
                  >
                    Execute Payment
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* ==================================================
          AUDIT LOGS
          ================================================== */}
      {isAdmin && (
        <div
          className="audit-panel"
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            padding: "16px 18px",
            borderRadius: "12px",
            marginTop: "22px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "20px",
              flexWrap: "wrap",
              gap: "10px",
            }}
          >
            <div>
              <h2 style={{ margin: 0, fontSize: "19px", fontWeight: 650, letterSpacing: "-0.02em" }}>Audit Logs</h2>
              <p style={{ margin: "5px 0 0", color: "#64748b", fontSize: "14px" }}>
                Administrative actions performed on transactions.
              </p>
            </div>

            <button
              onClick={fetchAuditLogs}
              style={{
                ...buttonStyle,
                background: "#ffffff",
                color: "#475569",
              }}
            >
              {auditLoading
                ? "Loading..."
                : "Refresh Logs"}
            </button>
          </div>

          {auditLogs.length === 0 ? (
            <div
              style={{
                padding: "20px",
                background: "#f9fafb",
                borderRadius: "8px",
              }}
            >
              <p>No audit logs found.</p>
            </div>
          ) : (
            <div
              style={{
                overflowX: "auto",
              }}
            >
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  minWidth: "750px",
                }}
              >
                <thead>
                  <tr>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "12px",
                        borderBottom:
                          "1px solid #d1d5db",
                      }}
                    >
                      ID
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "12px",
                        borderBottom:
                          "1px solid #d1d5db",
                      }}
                    >
                      User
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "12px",
                        borderBottom:
                          "1px solid #d1d5db",
                      }}
                    >
                      Transaction
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "12px",
                        borderBottom:
                          "1px solid #d1d5db",
                      }}
                    >
                      Action
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "12px",
                        borderBottom:
                          "1px solid #d1d5db",
                      }}
                    >
                      Old Status
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "12px",
                        borderBottom:
                          "1px solid #d1d5db",
                      }}
                    >
                      New Status
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "12px",
                        borderBottom:
                          "1px solid #d1d5db",
                      }}
                    >
                      Time
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td
                        style={{
                          padding: "12px",
                          borderBottom:
                            "1px solid #e2e8f0",
                        }}
                      >
                        {log.id}
                      </td>

                      <td
                        style={{
                          padding: "12px",
                          borderBottom:
                            "1px solid #e2e8f0",
                        }}
                      >
                        {log.user_id}
                      </td>

                      <td
                        style={{
                          padding: "12px",
                          borderBottom:
                            "1px solid #e2e8f0",
                        }}
                      >
                        #{log.transaction_id}
                      </td>

                      <td
                        style={{
                          padding: "12px",
                          borderBottom:
                            "1px solid #e2e8f0",
                          fontWeight: "600",
                        }}
                      >
                        {log.action}
                      </td>

                      <td
                        style={{
                          padding: "12px",
                          borderBottom:
                            "1px solid #e2e8f0",
                        }}
                      >
                        {log.old_status || "-"}
                      </td>

                      <td
                        style={{
                          padding: "12px",
                          borderBottom:
                            "1px solid #e2e8f0",
                        }}
                      >
                        {log.new_status || "-"}
                      </td>

                      <td
                        style={{
                          padding: "12px",
                          borderBottom:
                            "1px solid #e2e8f0",
                        }}
                      >
                        {log.created_at
                          ? new Date(
                              log.created_at
                            ).toLocaleString("en-IN")
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;