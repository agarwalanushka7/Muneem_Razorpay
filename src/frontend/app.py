import requests
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="AI Revenue Agent",
    page_icon="🤖",
    layout="wide",
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULT_STATE = {
    "upload_result": None,
    "import_result": None,
    "selected_file_name": None,
    "dashboard": None,
    "opportunities": [],
    "agent_analysis": {},
    "agent_actions": {},
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# API HELPERS
# =========================================================


def get_dashboard_data():

    try:

        response = requests.get(
            f"{API_URL}/dashboard/summary",
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()

        return None

    except requests.exceptions.RequestException:

        return None


def get_opportunities():

    try:

        response = requests.get(
            f"{API_URL}/opportunities/",
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()

        return []

    except requests.exceptions.RequestException:

        return []


def detect_opportunities():

    try:

        response = requests.post(
            f"{API_URL}/opportunities/detect",
            timeout=60,
        )

        if response.status_code == 200:

            result = response.json()

            st.session_state[
                "opportunities"
            ] = result.get(
                "opportunities",
                [],
            )

            return result

        return None

    except requests.exceptions.RequestException:

        return None


# =========================================================
# AI AGENT HELPERS
# =========================================================


def analyze_opportunity(
    opportunity_id: int,
):

    try:

        response = requests.post(
            f"{API_URL}/agent/analyze/{opportunity_id}",
            timeout=180,
        )

        if response.status_code == 200:

            return response.json()

        st.error(
            "AI analysis failed."
        )

        st.code(
            response.text
        )

        return None

    except requests.exceptions.RequestException as e:

        st.error(
            "Could not connect to the AI Revenue Agent."
        )

        st.code(
            str(e)
        )

        return None


def create_agent_action(
    opportunity_id: int,
):

    try:

        response = requests.post(
            f"{API_URL}/agent-actions/create/{opportunity_id}",
            timeout=180,
        )

        if response.status_code == 200:

            return response.json()

        st.error(
            "Could not create the agent action."
        )

        st.code(
            response.text
        )

        return None

    except requests.exceptions.RequestException as e:

        st.error(
            "Could not connect to the Agent Action API."
        )

        st.code(
            str(e)
        )

        return None


def approve_agent_action(
    action_id: int,
):

    try:

        response = requests.post(
            f"{API_URL}/agent-actions/{action_id}/approve",
            timeout=60,
        )

        if response.status_code == 200:

            return response.json()

        st.error(
            "Could not approve the agent action."
        )

        st.code(
            response.text
        )

        return None

    except requests.exceptions.RequestException as e:

        st.error(
            "Could not connect to the Agent Action API."
        )

        st.code(
            str(e)
        )

        return None


def reject_agent_action(
    action_id: int,
):

    try:

        response = requests.post(
            f"{API_URL}/agent-actions/{action_id}/reject",
            timeout=60,
        )

        if response.status_code == 200:

            return response.json()

        st.error(
            "Could not reject the agent action."
        )

        st.code(
            response.text
        )

        return None

    except requests.exceptions.RequestException as e:

        st.error(
            "Could not connect to the Agent Action API."
        )

        st.code(
            str(e)
        )

        return None


def execute_agent_action(
    action_id: int,
):

    try:

        response = requests.post(
            f"{API_URL}/agent-actions/{action_id}/execute",
            timeout=60,
        )

        if response.status_code == 200:

            return response.json()

        st.error(
            "Could not execute the agent action."
        )

        st.code(
            response.text
        )

        return None

    except requests.exceptions.RequestException as e:

        st.error(
            "Could not connect to the Agent Action API."
        )

        st.code(
            str(e)
        )

        return None


# =========================================================
# DISPLAY AI ANALYSIS
# =========================================================


def display_agent_analysis(
    opportunity_id: int,
):

    analysis = st.session_state[
        "agent_analysis"
    ].get(
        str(opportunity_id)
    )

    if not analysis:
        return

    st.divider()

    st.subheader(
        "🧠 AI Revenue Agent Analysis"
    )

    ai_decision = analysis.get(
        "ai_decision",
        {},
    )

    investigation = analysis.get(
        "agent_investigation",
        {},
    )

    opportunity = analysis.get(
        "opportunity",
        {},
    )

    # -----------------------------------------------------
    # AI DECISION
    # -----------------------------------------------------

    st.markdown(
        "### AI Recommendation"
    )

    action = ai_decision.get(
        "action",
        "no_action",
    )

    reason = ai_decision.get(
        "reason",
        "No reasoning provided.",
    )

    confidence = ai_decision.get(
        "confidence"
    )

    suggested_amount = ai_decision.get(
        "suggested_amount"
    )

    expected_impact = ai_decision.get(
        "expected_revenue_impact"
    )

    st.info(
        f"**Recommended action:** "
        f"`{action}`\n\n"
        f"**Why:** {reason}"
    )

    # -----------------------------------------------------
    # AI METRICS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        if confidence is not None:

            st.metric(
                "AI Confidence",
                f"{float(confidence) * 100:.0f}%",
            )

        else:

            st.metric(
                "AI Confidence",
                "N/A",
            )

    with col2:

        if suggested_amount is not None:

            st.metric(
                "Suggested Amount",
                f"₹{float(suggested_amount):,.2f}",
            )

        else:

            st.metric(
                "Suggested Amount",
                "N/A",
            )

    with col3:

        if expected_impact is not None:

            st.metric(
                "Expected Revenue Impact",
                f"₹{float(expected_impact):,.2f}",
            )

        else:

            st.metric(
                "Expected Revenue Impact",
                "N/A",
            )

    # -----------------------------------------------------
    # DISCOUNT
    # -----------------------------------------------------

    discount = ai_decision.get(
        "discount_percentage"
    )

    if discount is not None:

        st.write(
            f"**Suggested discount:** "
            f"{discount}%"
        )

    # -----------------------------------------------------
    # INVESTIGATION
    # -----------------------------------------------------

    with st.expander(
        "🔍 View Agent Investigation"
    ):

        if investigation:

            st.json(
                investigation
            )

        else:

            st.write(
                "No additional investigation data."
            )

    # -----------------------------------------------------
    # POLICY
    # -----------------------------------------------------

    policy = analysis.get(
        "policy",
        {},
    )

    if policy:

        st.markdown(
            "### 🛡️ Merchant Policy"
        )

        policy_allowed = policy.get(
            "allowed",
            False,
        )

        requires_approval = policy.get(
            "requires_approval",
            False,
        )

        policy_reason = policy.get(
            "reason",
            "",
        )

        if requires_approval:

            st.warning(
                "⚠️ Merchant approval is required."
            )

        elif policy_allowed:

            st.success(
                "✅ Action is allowed by merchant policy."
            )

        else:

            st.error(
                "❌ Action is not allowed by merchant policy."
            )

        if policy_reason:

            st.caption(
                policy_reason
            )

    # -----------------------------------------------------
    # CREATE ACTION
    # -----------------------------------------------------

    if action == "no_action":

        st.info(
            "The AI decided that no action is required."
        )

        return

    agent_action = st.session_state[
        "agent_actions"
    ].get(
        str(opportunity_id)
    )

    if not agent_action:

        st.divider()

        if st.button(
            "⚡ Create AI Action",
            key=f"create_action_{opportunity_id}",
            type="primary",
        ):

            with st.spinner(
                "Creating AI action..."
            ):

                result = create_agent_action(
                    opportunity_id
                )

            if result:

                st.session_state[
                    "agent_actions"
                ][
                    str(opportunity_id)
                ] = result

                st.rerun()

        return

    # -----------------------------------------------------
    # ACTION STATUS
    # -----------------------------------------------------

    display_agent_action(
        opportunity_id,
        agent_action,
    )


# =========================================================
# DISPLAY AGENT ACTION
# =========================================================


def display_agent_action(
    opportunity_id: int,
    action_data: dict,
):

    st.divider()

    st.markdown(
        "### 🤖 Agent Action"
    )

    action_id = action_data.get(
        "action_id"
    )

    action_type = action_data.get(
        "action_type",
        "unknown",
    )

    action_amount = action_data.get(
        "action_amount",
        0,
    )

    status = action_data.get(
        "status",
        "unknown",
    )

    approval_required = action_data.get(
        "approval_required",
        False,
    )

    st.write(
        f"**Action:** `{action_type}`"
    )

    st.write(
        f"**Action amount:** "
        f"₹{float(action_amount):,.2f}"
    )

    # -----------------------------------------------------
    # PENDING APPROVAL
    # -----------------------------------------------------

    if status == "pending_approval":

        st.warning(
            "⚠️ This action requires merchant approval."
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "✅ Approve",
                key=f"approve_{action_id}",
                type="primary",
            ):

                with st.spinner(
                    "Approving action..."
                ):

                    result = approve_agent_action(
                        action_id
                    )

                if result:

                    st.session_state[
                        "agent_actions"
                    ][
                        str(opportunity_id)
                    ] = {
                        **action_data,
                        **result,
                        "status": "approved",
                    }

                    st.success(
                        "Agent action approved."
                    )

                    st.rerun()

        with col2:

            if st.button(
                "❌ Reject",
                key=f"reject_{action_id}",
            ):

                with st.spinner(
                    "Rejecting action..."
                ):

                    result = reject_agent_action(
                        action_id
                    )

                if result:

                    st.session_state[
                        "agent_actions"
                    ][
                        str(opportunity_id)
                    ] = {
                        **action_data,
                        **result,
                        "status": "rejected",
                    }

                    st.warning(
                        "Agent action rejected."
                    )

                    st.rerun()

    # -----------------------------------------------------
    # APPROVED
    # -----------------------------------------------------

    elif status == "approved":

        st.success(
            "✅ Agent action approved by merchant."
        )

        st.info(
            "The action is ready for execution."
        )

        if st.button(
            "🚀 Execute Action",
            key=f"execute_{action_id}",
            type="primary",
        ):

            with st.spinner(
                "Executing AI action..."
            ):

                result = execute_agent_action(
                    action_id
                )

            if result:

                st.session_state[
                    "agent_actions"
                ][
                    str(opportunity_id)
                ] = {
                    **action_data,
                    **result,
                    "status": "EXECUTED",
                }

                st.success(
                    "🎉 Agent action executed successfully!"
                )

                st.rerun()

    # -----------------------------------------------------
    # EXECUTED
    # -----------------------------------------------------

    elif status == "EXECUTED":

        st.success(
            "🎉 AI action executed successfully."
        )

        st.write(
            "The merchant-approved revenue action "
            "has been completed."
        )

    # -----------------------------------------------------
    # REJECTED
    # -----------------------------------------------------

    elif status == "rejected":

        st.error(
            "❌ Merchant rejected this action."
        )

    # -----------------------------------------------------
    # AUTO EXECUTE
    # -----------------------------------------------------

    elif status == "auto_execute":

        st.info(
            "This action is eligible for automatic execution."
        )

        if action_id:

            if st.button(
                "🚀 Execute Action",
                key=f"auto_execute_{action_id}",
                type="primary",
            ):

                with st.spinner(
                    "Executing action..."
                ):

                    result = execute_agent_action(
                        action_id
                    )

                if result:

                    st.session_state[
                        "agent_actions"
                    ][
                        str(opportunity_id)
                    ] = {
                        **action_data,
                        **result,
                        "status": "EXECUTED",
                    }

                    st.success(
                        "🎉 Agent action executed."
                    )

                    st.rerun()

    else:

        st.info(
            f"Current action status: `{status}`"
        )


# =========================================================
# DISPLAY OPPORTUNITY
# =========================================================


def display_opportunity(
    opportunity: dict,
    button_text: str = "🧠 Analyze with AI",
):

    opportunity_id = opportunity.get(
        "id"
    )

    if opportunity_id is None:

        return

    with st.container(
        border=True
    ):

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        st.subheader(
            opportunity.get(
                "title",
                "Revenue Opportunity",
            )
        )

        # -------------------------------------------------
        # DESCRIPTION
        # -------------------------------------------------

        st.write(
            opportunity.get(
                "description",
                "",
            )
        )

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Customers",
                opportunity.get(
                    "customer_count",
                    0,
                ),
            )

        with col2:

            st.metric(
                "Potential Revenue",
                (
                    "₹"
                    + f"{float(opportunity.get('estimated_value', 0)):,.2f}"
                ),
            )

        with col3:

            st.metric(
                "Confidence",
                opportunity.get(
                    "confidence",
                    "Unknown",
                ),
            )

        st.caption(
            "Type: "
            + opportunity.get(
                "opportunity_type",
                opportunity.get(
                    "type",
                    "unknown",
                ),
            )
        )

        st.divider()

        # -------------------------------------------------
        # ANALYZE BUTTON
        # -------------------------------------------------

        analysis_exists = (
            str(opportunity_id)
            in st.session_state[
                "agent_analysis"
            ]
        )

        if not analysis_exists:

            if st.button(
                button_text,
                key=f"analyze_{opportunity_id}",
                type="primary",
            ):

                with st.spinner(
                    "🤖 Revenue Agent is investigating this opportunity..."
                ):

                    result = analyze_opportunity(
                        opportunity_id
                    )

                if result:

                    st.session_state[
                        "agent_analysis"
                    ][
                        str(opportunity_id)
                    ] = result

                    st.rerun()

        else:

            st.success(
                "✅ AI analysis completed."
            )

        # -------------------------------------------------
        # SHOW AI ANALYSIS
        # -------------------------------------------------

        display_agent_analysis(
            opportunity_id
        )


# =========================================================
# TITLE
# =========================================================

st.title(
    "🤖 AI Revenue Agent"
)

st.caption(
    "Understand your business, discover revenue "
    "opportunities, and take AI-assisted action."
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header(
        "Merchant Console"
    )

    page = st.radio(
        "Navigate",
        [
            "Dashboard",
            "Import Business Data",
            "AI Opportunities",
        ],
    )

    st.divider()

    st.caption(
        "AI Revenue Agent • Merchant Console"
    )


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.title(
        "Revenue Dashboard"
    )

    st.write(
        "Understand your business and discover "
        "revenue opportunities with AI."
    )

    dashboard = get_dashboard_data()

    if dashboard is None:

        st.error(
            "Could not connect to the backend."
        )

        st.info(
            "Make sure FastAPI is running on "
            "http://127.0.0.1:8000"
        )

    else:

        st.session_state[
            "dashboard"
        ] = dashboard

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Revenue",
                f"₹{dashboard.get('total_revenue', 0):,.2f}",
            )

        with col2:

            st.metric(
                "Total Orders",
                dashboard.get(
                    "total_orders",
                    0,
                ),
            )

        with col3:

            st.metric(
                "Customers",
                dashboard.get(
                    "total_customers",
                    0,
                ),
            )

        with col4:

            st.metric(
                "Products",
                dashboard.get(
                    "total_products",
                    0,
                ),
            )

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Inventory",
                dashboard.get(
                    "total_inventory",
                    0,
                ),
            )

        with col2:

            st.metric(
                "Average Order Value",
                f"₹{dashboard.get('average_order_value', 0):,.2f}",
            )

        with col3:

            st.metric(
                "Transactions",
                dashboard.get(
                    "total_transactions",
                    0,
                ),
            )

        st.divider()

        # -------------------------------------------------
        # OPPORTUNITIES
        # -------------------------------------------------

        st.header(
            "🤖 AI Revenue Opportunities"
        )

        opportunities = get_opportunities()

        if not opportunities:

            st.info(
                "No revenue opportunities found yet."
            )

            st.caption(
                "Import business data and run "
                "AI opportunity detection."
            )

        else:

            st.success(
                f"{len(opportunities)} revenue "
                "opportunit"
                + (
                    "y detected."
                    if len(opportunities) == 1
                    else "ies detected."
                )
            )

            for opportunity in opportunities:

                display_opportunity(
                    opportunity
                )


# =========================================================
# IMPORT BUSINESS DATA
# =========================================================

elif page == "Import Business Data":

    st.title(
        "📂 Import Business Data"
    )

    st.write(
        "Upload your existing business data. "
        "The AI will understand the structure "
        "before anything is imported."
    )

    # -----------------------------------------------------
    # FILE UPLOAD
    # -----------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload your business file",
        type=[
            "csv",
            "xlsx",
            "xls",
            "pdf",
        ],
        help=(
            "Supported formats: CSV, Excel, PDF"
        ),
    )

    if uploaded_file is not None:

        st.success(
            f"Selected: {uploaded_file.name}"
        )

        # -------------------------------------------------
        # ANALYZE
        # -------------------------------------------------

        if st.button(
            "🔎 Analyze File",
            type="primary",
        ):

            try:

                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                }

                with st.spinner(
                    "AI is analyzing your business data..."
                ):

                    response = requests.post(
                        f"{API_URL}/data/upload",
                        files=files,
                        timeout=180,
                    )

                if response.status_code == 200:

                    result = response.json()

                    st.session_state[
                        "upload_result"
                    ] = result

                    st.session_state[
                        "import_result"
                    ] = None

                    st.success(
                        "File analyzed successfully."
                    )

                else:

                    st.error(
                        "File analysis failed."
                    )

                    st.code(
                        response.text
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to FastAPI."
                )

                st.info(
                    "Start the backend with:\n\n"
                    "python -m uvicorn "
                    "src.backend.main:app --reload"
                )

            except Exception as e:

                st.error(
                    f"Unexpected error: {e}"
                )

    # -----------------------------------------------------
    # AI ANALYSIS RESULT
    # -----------------------------------------------------

    result = st.session_state.get(
        "upload_result"
    )

    if result:

        st.divider()

        st.header(
            "🧠 AI Data Understanding"
        )

        st.write(
            f"**File:** "
            f"{result.get('filename', 'Unknown')}"
        )

        st.write(
            f"**Type:** "
            f"{result.get('file_type', 'Unknown')}"
        )

        st.write(
            f"**Upload ID:** "
            f"{result.get('upload_id', 'Unknown')}"
        )

        mapping_data = result.get(
            "ai_mapping",
            {},
        )

        dataset_type = mapping_data.get(
            "dataset_type",
            "unknown",
        )

        st.write(
            f"**Detected dataset:** `{dataset_type}`"
        )

        explanation = mapping_data.get(
            "explanation",
            "",
        )

        if explanation:

            st.info(
                explanation
            )

        # -------------------------------------------------
        # FIELD MAPPING
        # -------------------------------------------------

        st.subheader(
            "AI Generated Field Mapping"
        )

        mappings = mapping_data.get(
            "mappings",
            [],
        )

        if mappings:

            for mapping in mappings:

                source = mapping.get(
                    "source_column",
                    "",
                )

                target = mapping.get(
                    "target_field",
                    "",
                )

                confidence = mapping.get(
                    "confidence",
                    0,
                )

                col1, col2, col3 = st.columns(
                    [3, 1, 1]
                )

                with col1:

                    st.write(
                        f"**{source}**"
                    )

                with col2:

                    st.write(
                        "→ "
                        f"`{target}`"
                    )

                with col3:

                    st.write(
                        f"{confidence * 100:.0f}%"
                    )

        else:

            st.warning(
                "The AI did not generate any "
                "field mappings."
            )

        st.divider()

        st.warning(
            "Please review the AI-generated "
            "mapping before importing."
        )

        # -------------------------------------------------
        # CONFIRM IMPORT
        # -------------------------------------------------

        if st.button(
            "✅ Confirm & Import",
            type="primary",
        ):

            upload_id = result.get(
                "upload_id"
            )

            if not upload_id:

                st.error(
                    "Upload ID is missing."
                )

            else:

                mappings_for_api = []

                for mapping in mappings:

                    mappings_for_api.append(
                        {
                            "source_column": mapping.get(
                                "source_column"
                            ),
                            "target_field": mapping.get(
                                "target_field"
                            ),
                        }
                    )

                payload = {
                    "dataset_type": dataset_type,
                    "mappings": mappings_for_api,
                }

                try:

                    with st.spinner(
                        "Importing business data and "
                        "detecting opportunities..."
                    ):

                        response = requests.post(
                            (
                                f"{API_URL}"
                                f"/data/upload/"
                                f"{upload_id}"
                                f"/confirm"
                            ),
                            json=payload,
                            timeout=180,
                        )

                    if response.status_code == 200:

                        import_result = (
                            response.json()
                        )

                        st.session_state[
                            "import_result"
                        ] = import_result

                        st.session_state[
                            "dashboard"
                        ] = get_dashboard_data()

                        st.session_state[
                            "opportunities"
                        ] = get_opportunities()

                        st.success(
                            "🎉 Business data imported "
                            "successfully!"
                        )

                    else:

                        st.error(
                            "Import failed."
                        )

                        st.code(
                            response.text
                        )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "Could not connect to FastAPI."
                    )

                except Exception as e:

                    st.error(
                        f"Unexpected error: {e}"
                    )

    # -----------------------------------------------------
    # IMPORT SUMMARY
    # -----------------------------------------------------

    import_result = st.session_state.get(
        "import_result"
    )

    if import_result:

        st.divider()

        st.header(
            "Import Summary"
        )

        import_data = import_result.get(
            "import",
            {},
        )

        col1, col2, col3, col4 = st.columns(
            4
        )

        with col1:

            st.metric(
                "Customers",
                import_data.get(
                    "customers_imported",
                    0,
                ),
            )

        with col2:

            st.metric(
                "Products",
                import_data.get(
                    "products_imported",
                    0,
                ),
            )

        with col3:

            st.metric(
                "Orders",
                import_data.get(
                    "orders_imported",
                    0,
                ),
            )

        with col4:

            st.metric(
                "Transactions",
                import_data.get(
                    "transactions_imported",
                    0,
                ),
            )

        skipped = import_data.get(
            "skipped",
            0,
        )

        duplicates = (
            import_data.get(
                "order_duplicates",
                0,
            )
            + import_data.get(
                "transaction_duplicates",
                0,
            )
        )

        if skipped == 0:

            st.success(
                "No rows were skipped."
            )

        else:

            st.warning(
                f"{skipped} rows were skipped."
            )

        if duplicates > 0:

            st.info(
                f"{duplicates} existing records "
                "were detected and not duplicated."
            )

        # -------------------------------------------------
        # OPPORTUNITIES FOUND DURING IMPORT
        # -------------------------------------------------

        detected_count = (
            import_result.get(
                "opportunities_detected",
                0,
            )
        )

        st.divider()

        st.header(
            "🤖 AI Revenue Opportunities"
        )

        if detected_count == 0:

            st.info(
                "No new revenue opportunities "
                "were detected from this import."
            )

        else:

            st.success(
                f"{detected_count} revenue "
                "opportunit"
                + (
                    "y detected."
                    if detected_count == 1
                    else "ies detected."
                )
            )

            imported_opportunities = (
                import_result.get(
                    "opportunities",
                    [],
                )
            )

            for opportunity in imported_opportunities:

                display_opportunity(
                    opportunity
                )


# =========================================================
# AI OPPORTUNITIES PAGE
# =========================================================

elif page == "AI Opportunities":

    st.title(
        "🤖 AI Revenue Opportunities"
    )

    st.write(
        "Revenue opportunities detected from "
        "your merchant data."
    )

    opportunities = get_opportunities()

    if not opportunities:

        st.info(
            "No revenue opportunities found yet."
        )

        st.write(
            "Import your business data first."
        )

        if st.button(
            "🔎 Run Opportunity Detection"
        ):

            with st.spinner(
                "Analyzing merchant data..."
            ):

                result = detect_opportunities()

            if result:

                count = result.get(
                    "count",
                    0,
                )

                if count > 0:

                    st.success(
                        f"{count} opportunities detected."
                    )

                    st.rerun()

                else:

                    st.info(
                        "No qualifying revenue "
                        "opportunities were found."
                    )

            else:

                st.error(
                    "Opportunity detection failed."
                )

    else:

        st.success(
            f"{len(opportunities)} revenue "
            "opportunities available."
        )

        for opportunity in opportunities:

            display_opportunity(
                opportunity,
                button_text="🧠 Analyze with Revenue Agent",
            )