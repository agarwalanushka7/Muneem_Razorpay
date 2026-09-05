import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Revenue from "./pages/Revenue";
import Products from "./pages/Products";
import Orders from "./pages/Orders";
import Customers from "./pages/Customers";
import AgentActions from "./pages/AgentActions";
import Platforms from "./pages/Platforms";
import Audit from "./pages/Audit";

import Header from "./components/Header";
import Sidebar from "./components/Sidebar";


/* =========================================================
   AUTH GUARD
   ========================================================= */

function ProtectedRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const isAuthenticated =
    localStorage.getItem("muneem_authenticated") === "true";

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  return <>{children}</>;
}


/* =========================================================
   MERCHANT APP LAYOUT
   ========================================================= */

function AppLayout() {
  return (
    <ProtectedRoute>

      <div className="muneem-app">

        <Header />

        <div className="muneem-layout">

          <Sidebar />

          <main className="muneem-main">

            <Routes>

              <Route
                path="/dashboard"
                element={<Dashboard />}
              />

              <Route
                path="/revenue"
                element={<Revenue />}
              />

              <Route
                path="/products"
                element={<Products />}
              />

              <Route
                path="/orders"
                element={<Orders />}
              />

              <Route
                path="/customers"
                element={<Customers />}
              />

              <Route
                path="/agent-actions"
                element={<AgentActions />}
              />

              <Route
                path="/platforms"
                element={<Platforms />}
              />

              <Route
                path="/audit"
                element={<Audit />}
              />

              <Route
                path="*"
                element={
                  <Navigate
                    to="/dashboard"
                    replace
                  />
                }
              />

            </Routes>

          </main>

        </div>

      </div>

    </ProtectedRoute>
  );
}


/* =========================================================
   APP
   ========================================================= */

function App() {
  return (
    <BrowserRouter>

      <Routes>

        {/* PUBLIC LOGIN */}

        <Route
          path="/"
          element={<Login />}
        />


        {/* PROTECTED MERCHANT CONSOLE */}

        <Route
          path="/*"
          element={<AppLayout />}
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;