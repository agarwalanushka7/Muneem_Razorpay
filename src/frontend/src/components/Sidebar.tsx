import { NavLink } from "react-router-dom";
import "./Sidebar.css";

function Sidebar() {
  const sections = [
    {
      title: "OVERVIEW",
      links: [
        {
          name: "Dashboard",
          path: "/dashboard",
        },
        {
          name: "Revenue",
          path: "/revenue",
        },
      ],
    },
    {
      title: "RECOVERY",
      links: [
        {
          name: "Agent Actions",
          path: "/agent-actions",
        },
        {
          name: "Orders",
          path: "/orders",
        },
      ],
    },
    {
      title: "COMMERCE",
      links: [
        {
          name: "Customers",
          path: "/customers",
        },
        {
          name: "Products",
          path: "/products",
        },
      ],
    },
    {
      title: "OPERATIONS",
      links: [
        {
          name: "Platforms",
          path: "/platforms",
        },
        {
          name: "Audit Log",
          path: "/audit",
        },
      ],
    },
  ];

  return (
    <aside className="muneem-sidebar">

      <div className="muneem-sidebar-inner">

        {sections.map((section) => (
          <section
            className="muneem-sidebar-section"
            key={section.title}
          >
            <p className="muneem-sidebar-label">
              {section.title}
            </p>

            <nav className="muneem-sidebar-nav">
              {section.links.map((link) => (
                <NavLink
                  key={link.path}
                  to={link.path}
                  end={link.path === "/dashboard"}
                  className={({ isActive }) =>
                    `muneem-sidebar-link ${
                      isActive ? "active" : ""
                    }`
                  }
                >
                  <span className="muneem-sidebar-link-text">
                    {link.name}
                  </span>

                  <span className="muneem-sidebar-arrow">
                    →
                  </span>
                </NavLink>
              ))}
            </nav>
          </section>
        ))}

      </div>

      <div className="muneem-sidebar-bottom">

        <div className="muneem-agent-card">

          <div className="muneem-agent-card-title">
            <span className="muneem-live-dot" />

            <span>
              AI REVENUE AGENT
            </span>
          </div>

          <p>
            Watching your revenue and surfacing
            opportunities that need your attention.
          </p>

          <NavLink
            to="/agent-actions"
            className="muneem-agent-link"
          >
            <span>VIEW AGENT</span>

            <span className="muneem-agent-link-arrow">
              ↗
            </span>
          </NavLink>

        </div>

        <div className="muneem-sidebar-footer">
          MUNEEM · MERCHANT CONSOLE
        </div>

      </div>

    </aside>
  );
}

export default Sidebar;