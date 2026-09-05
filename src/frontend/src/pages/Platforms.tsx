import { useEffect, useRef, useState } from "react";
import "./Platforms.css";

interface Platform {
  id: number;
  name: string;
  display_name: string;
  platform_type: string;
  connection_type: string;
  status: string;
  is_active: boolean;
  last_synced_at: string | null;
  created_at: string;
}

interface AvailableChannel {
  name: string;
  display_name: string;
  platform_type: string;
  connection_type: string;
  description: string;
  import_types: string[];
}

interface Mapping {
  source_column: string;
  target_field: string;
  confidence?: number;
}

interface UploadResult {
  success: boolean;
  upload_id: string;
  filename: string;
  file_type?: string;
  data?: {
    rows?: number;
    columns?: string[];
    preview?: Record<string, unknown>[];
  };
  ai_mapping?: {
    dataset_type?: string;
    explanation?: string;
    mappings?: Mapping[];
  };
  message?: string;
}

const API_URL = "http://127.0.0.1:8000";

function Platforms() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [channels, setChannels] = useState<AvailableChannel[]>([]);

  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [selectedPlatform, setSelectedPlatform] =
    useState<Platform | null>(null);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const [uploadResult, setUploadResult] =
    useState<UploadResult | null>(null);

  const fileInputRef =
    useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    loadPlatforms();
  }, []);

  async function loadPlatforms() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_URL}/platforms`
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load sales channels."
        );
      }

      const data = await response.json();

      setPlatforms(
        Array.isArray(data) ? data : []
      );

      setChannels([
        {
          name: "direct",
          display_name: "Direct Store",
          platform_type: "native",
          connection_type: "native",
          description:
            "Connect your own store data.",
          import_types: [
            "xlsx",
            "xls",
            "csv",
            "pdf",
          ],
        },
        {
          name: "blinkit",
          display_name: "Blinkit",
          platform_type: "marketplace",
          connection_type: "manual",
          description:
            "Import your Blinkit sales export.",
          import_types: [
            "xlsx",
            "xls",
            "csv",
            "pdf",
          ],
        },
        {
          name: "zepto",
          display_name: "Zepto",
          platform_type: "marketplace",
          connection_type: "manual",
          description:
            "Import your Zepto sales export.",
          import_types: [
            "xlsx",
            "xls",
            "csv",
            "pdf",
          ],
        },
      ]);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load channels."
      );
    } finally {
      setLoading(false);
    }
  }

  function clearMessages() {
    setMessage("");
    setError("");
  }

  function getConnectedPlatform(
    channelName: string
  ) {
    return platforms.find(
      (platform) =>
        platform.name.toLowerCase() ===
        channelName.toLowerCase()
    );
  }

  async function connectChannel(
    channel: AvailableChannel
  ) {
    try {
      clearMessages();
      setConnecting(channel.name);

      const existing =
        getConnectedPlatform(channel.name);

      if (existing) {
        const response = await fetch(
          `${API_URL}/platforms/${existing.id}/connect`,
          {
            method: "POST",
          }
        );

        const data =
          await response.json().catch(() => null);

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              "Unable to connect this channel."
          );
        }

        setMessage(
          `${channel.display_name} is now connected.`
        );

        await loadPlatforms();
        return;
      }

      const response = await fetch(
        `${API_URL}/platforms`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: channel.name,
            display_name: channel.display_name,
            platform_type:
              channel.platform_type,
            connection_type:
              channel.connection_type,
          }),
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to connect this channel."
        );
      }

      setMessage(
        `${channel.display_name} connected successfully.`
      );

      await loadPlatforms();
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect channel."
      );
    } finally {
      setConnecting(null);
    }
  }

  async function disconnectChannel(
    platform: Platform
  ) {
    try {
      clearMessages();

      const response = await fetch(
        `${API_URL}/platforms/${platform.id}/disconnect`,
        {
          method: "POST",
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to disconnect channel."
        );
      }

      if (
        selectedPlatform?.id === platform.id
      ) {
        closeImport();
      }

      setMessage(
        `${platform.display_name} disconnected.`
      );

      await loadPlatforms();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to disconnect channel."
      );
    }
  }

  function openImport(platform: Platform) {
    clearMessages();

    setSelectedPlatform(platform);
    setSelectedFile(null);
    setUploadResult(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function closeImport() {
    setSelectedPlatform(null);
    setSelectedFile(null);
    setUploadResult(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    clearMessages();
  }

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    clearMessages();

    const file =
      event.target.files?.[0] || null;

    setSelectedFile(file);
    setUploadResult(null);
  }

  async function analyzeFile() {
    if (!selectedPlatform) {
      setError(
        "Please select a sales channel first."
      );
      return;
    }

    if (!selectedFile) {
      setError(
        "Please choose a CSV, Excel or PDF file."
      );
      return;
    }

    try {
      setUploading(true);
      clearMessages();
      setUploadResult(null);

      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );

      console.log(
        "Uploading file:",
        selectedFile.name,
        selectedFile.type,
        selectedFile.size
      );

      const response = await fetch(
        `${API_URL}/data/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const responseText =
        await response.text();

      let data: UploadResult | null =
        null;

      try {
        data = responseText
          ? JSON.parse(responseText)
          : null;
      } catch {
        data = null;
      }

      console.log(
        "ANALYZE FILE STATUS:",
        response.status
      );

      console.log(
        "ANALYZE FILE RESPONSE:",
        responseText
      );

      if (!response.ok) {
        throw new Error(
          data?.message ||
          (data as any)?.detail ||
          responseText ||
          `Upload failed with status ${response.status}.`
        );
      }

      if (!data?.success) {
        throw new Error(
          data?.message ||
          "MUNEEM could not analyze this file."
        );
      }

      if (!data.upload_id) {
        throw new Error(
          "The file was analyzed, but MUNEEM did not receive an upload ID."
        );
      }

      setUploadResult(data);

      setMessage(
        "File analyzed successfully. Review the mapping below, then confirm the import."
      );
    } catch (err) {
      console.error(
        "ANALYZE FILE ERROR:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to analyze file."
      );
    } finally {
      setUploading(false);
    }
  }

  async function confirmImport() {
    if (!selectedPlatform) {
      setError(
        "No sales channel is selected."
      );
      return;
    }

    if (!uploadResult?.upload_id) {
      setError(
        "No analyzed file is available."
      );
      return;
    }

    try {
      setConfirming(true);
      clearMessages();

      const mappings =
        uploadResult.ai_mapping?.mappings || [];

      const datasetType =
        uploadResult.ai_mapping?.dataset_type ||
        "unknown";

      const response = await fetch(
        `${API_URL}/data/upload/${uploadResult.upload_id}/confirm`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            platform_id: selectedPlatform.id,
            dataset_type: datasetType,
            mappings: mappings.map(
              (mapping) => ({
                source_column:
                  mapping.source_column,
                target_field:
                  mapping.target_field,
              })
            ),
          }),
        }
      );

      const responseText =
        await response.text();

      let data: any = null;

      try {
        data = responseText
          ? JSON.parse(responseText)
          : null;
      } catch {
        data = null;
      }

      console.log(
        "CONFIRM IMPORT STATUS:",
        response.status
      );

      console.log(
        "CONFIRM IMPORT RESPONSE:",
        responseText
      );

      if (!response.ok) {
        throw new Error(
          data?.message ||
          data?.detail ||
          responseText ||
          `Import failed with status ${response.status}.`
        );
      }

      setMessage(
        data?.message ||
        `${selectedPlatform.display_name} data imported successfully.`
      );

      setSelectedFile(null);
      setUploadResult(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      await loadPlatforms();
    } catch (err) {
      console.error(
        "CONFIRM IMPORT ERROR:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to import data."
      );
    } finally {
      setConfirming(false);
    }
  }

  function formatDate(value: string | null) {
    if (!value) {
      return "No import yet";
    }

    return new Date(value).toLocaleString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  }

  if (loading) {
    return (
      <div className="platforms-loading">
        Loading channels...
      </div>
    );
  }

  const connectedCount =
    platforms.filter(
      (platform) => platform.is_active
    ).length;

  return (
    <div className="platforms-page">
      <section className="platforms-hero">
        <div className="platforms-meta">
          <span>05 / MUNEEM</span>
          <span>SALES CHANNELS</span>
        </div>

        <div className="platforms-hero-content">
          <div>
            <h1>
              Connect your
              <br />
              <em>channels.</em>
            </h1>
          </div>

          <div className="platforms-hero-copy">
            <strong>ONE COMMERCE VIEW</strong>

            <p>
              Bring the channels where your
              business sells into one MUNEEM
              workspace.
            </p>
          </div>

          <div className="platforms-count">
            <div>
              <span>AVAILABLE</span>
              <strong>{channels.length}</strong>
            </div>

            <div>
              <span>CONNECTED</span>
              <strong>{connectedCount}</strong>
            </div>
          </div>
        </div>
      </section>

      {(message || error) && (
        <div className="platform-notice">
          {message && (
            <div className="platform-success">
              <span>●</span>
              {message}
            </div>
          )}

          {error && (
            <div className="platform-error">
              <span>!</span>
              {error}
            </div>
          )}
        </div>
      )}

      <section className="channels-section">
        <div className="section-index">01</div>

        <div className="channels-intro">
          <span>SALES CHANNELS</span>

          <h2>
            Bring your commerce
            <br />
            <em>together.</em>
          </h2>

          <p>
            Connect a channel, then import
            its sales data. MUNEEM will use
            that information to understand
            customers, products and revenue
            opportunities.
          </p>
        </div>

        <div className="channels-grid">
          {channels.map(
            (channel, index) => {
              const platform =
                getConnectedPlatform(
                  channel.name
                );

              const connected =
                platform?.is_active === true;

              const busy =
                connecting === channel.name;

              return (
                <article
                  className={`channel-card ${
                    connected
                      ? "channel-card-connected"
                      : ""
                  }`}
                  key={channel.name}
                >
                  <div className="channel-card-header">
                    <span>
                      {String(index + 1).padStart(
                        2,
                        "0"
                      )}
                    </span>

                    <span
                      className={
                        connected
                          ? "channel-connected"
                          : "channel-available"
                      }
                    >
                      {connected
                        ? "CONNECTED"
                        : "AVAILABLE"}
                    </span>
                  </div>

                  <div className="channel-card-body">
                    <span className="channel-type">
                      {channel.connection_type ===
                      "native"
                        ? "NATIVE CHANNEL"
                        : "MANUAL IMPORT"}
                    </span>

                    <h3>
                      {channel.display_name}
                    </h3>

                    <p>
                      {channel.description}
                    </p>
                  </div>

                  <div className="channel-card-footer">
                    <div className="channel-formats">
                      {channel.import_types.map(
                        (type) => (
                          <span key={type}>
                            {type.toUpperCase()}
                          </span>
                        )
                      )}
                    </div>

                    {connected && platform ? (
                      <div className="channel-actions">
                        <button
                          type="button"
                          className="primary-channel-button"
                          onClick={() =>
                            openImport(platform)
                          }
                        >
                          IMPORT DATA
                          <span>→</span>
                        </button>

                        <button
                          type="button"
                          className="secondary-channel-button"
                          onClick={() =>
                            disconnectChannel(platform)
                          }
                        >
                          DISCONNECT
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        className="primary-channel-button"
                        disabled={busy}
                        onClick={() =>
                          connectChannel(channel)
                        }
                      >
                        {busy
                          ? "CONNECTING..."
                          : "CONNECT"}

                        {!busy && (
                          <span>→</span>
                        )}
                      </button>
                    )}
                  </div>
                </article>
              );
            }
          )}
        </div>
      </section>

      {selectedPlatform && (
        <div className="import-overlay">
          <div
            className="import-modal"
            role="dialog"
            aria-modal="true"
          >
            <div className="import-modal-header">
              <div>
                <span>DATA IMPORT</span>

                <h2>
                  Import{" "}
                  <em>
                    {selectedPlatform.display_name}
                  </em>{" "}
                  data.
                </h2>

                <p>
                  Upload a commerce export and
                  let MUNEEM understand its fields
                  before importing anything.
                </p>
              </div>

              <button
                type="button"
                className="import-close"
                onClick={closeImport}
              >
                ×
              </button>
            </div>

            {(message || error) && (
              <div
                className={`import-inline-notice ${
                  error
                    ? "import-inline-error"
                    : "import-inline-success"
                }`}
              >
                <span>
                  {error ? "!" : "●"}
                </span>

                <p>
                  {error || message}
                </p>
              </div>
            )}

            {!uploadResult && (
              <div className="import-step">
                <div className="step-label">
                  STEP 01
                </div>

                <h3>
                  Select your business data
                </h3>

                <p>
                  Supported formats: CSV, Excel
                  and PDF.
                </p>

                <label
                  htmlFor="muneem-file-input"
                  className="file-picker"
                >
                  <div className="file-plus">
                    +
                  </div>

                  <strong>
                    {selectedFile
                      ? selectedFile.name
                      : "Choose a file"}
                  </strong>

                  <span>
                    {selectedFile
                      ? `${(
                          selectedFile.size / 1024
                        ).toFixed(1)} KB`
                      : "Click to browse"}
                  </span>
                </label>

                <input
                  id="muneem-file-input"
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls,.pdf"
                  onChange={handleFileChange}
                />

                {selectedFile && !uploading && (
                  <p className="import-file-ready">
                    File selected. Click ANALYZE FILE
                    to upload it to MUNEEM.
                  </p>
                )}

                <div className="import-actions">
                  <button
                    type="button"
                    className="secondary-modal-button"
                    onClick={closeImport}
                  >
                    CANCEL
                  </button>

                  <button
                    type="button"
                    className="modal-primary-button"
                    disabled={
                      !selectedFile || uploading
                    }
                    onClick={analyzeFile}
                  >
                    {uploading
                      ? "ANALYZING..."
                      : "ANALYZE FILE"}

                    <span>→</span>
                  </button>
                </div>
              </div>
            )}

            {uploadResult && (
              <div className="analysis-container">
                <div className="analysis-header">
                  <div>
                    <span>
                      STEP 02 · MUNEEM ANALYSIS
                    </span>

                    <h3>
                      Review before importing.
                    </h3>
                  </div>

                  <span className="ready-label">
                    READY
                  </span>
                </div>

                <div className="analysis-summary">
                  <div>
                    <span>FILE</span>
                    <strong>
                      {uploadResult.filename}
                    </strong>
                  </div>

                  <div>
                    <span>DATASET</span>
                    <strong>
                      {uploadResult.ai_mapping
                        ?.dataset_type ||
                        "Unknown"}
                    </strong>
                  </div>

                  <div>
                    <span>ROWS</span>
                    <strong>
                      {uploadResult.data?.rows ??
                        "—"}
                    </strong>
                  </div>
                </div>

                {uploadResult.ai_mapping
                  ?.explanation && (
                  <div className="analysis-explanation">
                    <span>
                      MUNEEM'S INTERPRETATION
                    </span>

                    <p>
                      {
                        uploadResult.ai_mapping
                          .explanation
                      }
                    </p>
                  </div>
                )}

                <div className="mapping-table">
                  <div className="mapping-row mapping-heading">
                    <span>SOURCE</span>
                    <span>
                      MUNEEM UNDERSTANDS AS
                    </span>
                    <span>CONFIDENCE</span>
                  </div>

                  {(
                    uploadResult.ai_mapping
                      ?.mappings || []
                  ).map(
                    (mapping) => (
                      <div
                        className="mapping-row"
                        key={`${mapping.source_column}-${mapping.target_field}`}
                      >
                        <strong>
                          {mapping.source_column}
                        </strong>

                        <span>
                          →{" "}
                          {mapping.target_field}
                        </span>

                        <span className="confidence">
                          {Math.round(
                            (mapping.confidence || 0) *
                              100
                          )}
                          %
                        </span>
                      </div>
                    )
                  )}
                </div>

                <div className="analysis-warning">
                  <span>!</span>

                  <p>
                    MUNEEM will not import the
                    file until you confirm this
                    interpretation.
                  </p>
                </div>

                <div className="analysis-actions">
                  <button
                    type="button"
                    className="secondary-modal-button"
                    onClick={() =>
                      setUploadResult(null)
                    }
                  >
                    CHANGE FILE
                  </button>

                  <button
                    type="button"
                    className="modal-primary-button"
                    disabled={confirming}
                    onClick={confirmImport}
                  >
                    {confirming
                      ? "IMPORTING..."
                      : "CONFIRM & IMPORT"}

                    <span>→</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <section className="platforms-bottom">
        <div className="section-index">
          02
        </div>

        <div>
          <span className="eyebrow">
            THE MUNEEM DATA LAYER
          </span>

          <h2>
            One picture.
            <br />
            <em>Better decisions.</em>
          </h2>
        </div>

        <div className="bottom-copy">
          <p>
            Once connected, MUNEEM can reason
            across customers, products, orders
            and transactions to identify revenue
            opportunities.
          </p>

          <div className="bottom-points">
            <div>
              <strong>01</strong>
              CUSTOMER SIGNALS
            </div>

            <div>
              <strong>02</strong>
              COMMERCE INTELLIGENCE
            </div>

            <div>
              <strong>03</strong>
              REVENUE ACTIONS
            </div>
          </div>
        </div>
      </section>

      <footer className="platforms-footer">
        <span>CONNECT</span>
        <span>IMPORT</span>
        <span>GROW</span>

        <span className="footer-right">
          MUNEEM · MERCHANT CONSOLE · 2026
        </span>
      </footer>
    </div>
  );
}

export default Platforms;
