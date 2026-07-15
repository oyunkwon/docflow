import { useEffect, useState } from "react";

// nginx가 /api를 api 서비스로 프록시한다.
const API = "/api";

const STATUS_COLOR = {
  PENDING: "#9ca3af",
  PROCESSING: "#2563eb",
  COMPLETED: "#16a34a",
  FAILED: "#dc2626",
};

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const res = await fetch(`${API}/documents`);
      if (!res.ok) throw new Error(`list failed: ${res.status}`);
      setDocuments(await res.json());
    } catch (e) {
      setError(String(e));
    }
  }

  // 2초마다 목록을 폴링해 상태 변화를 반영한다.
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 2000);
    return () => clearInterval(id);
  }, []);

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    event.target.value = ""; // 같은 파일 재선택 허용
    if (!file) return;

    setUploading(true);
    setError("");
    try {
      // 1. presigned URL + 문서 행 생성
      const urlRes = await fetch(`${API}/documents/upload-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name }),
      });
      if (!urlRes.ok) throw new Error(`upload-url failed: ${urlRes.status}`);
      const { document_id, upload_url } = await urlRes.json();

      // 2. S3(로컬은 LocalStack)로 직접 PUT
      const putRes = await fetch(upload_url, {
        method: "PUT",
        headers: { "Content-Type": "application/pdf" },
        body: file,
      });
      if (!putRes.ok) throw new Error(`s3 put failed: ${putRes.status}`);

      // 3. 처리 요청 (SQS 발행)
      const doneRes = await fetch(`${API}/documents/${document_id}/complete`, {
        method: "POST",
      });
      if (!doneRes.ok) throw new Error(`complete failed: ${doneRes.status}`);

      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div style={{ maxWidth: 820, margin: "40px auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>DocFlow</h1>
      <p style={{ color: "#6b7280" }}>PDF를 올리면 워커가 메타데이터를 추출한다.</p>

      <label
        style={{
          display: "inline-block",
          padding: "10px 16px",
          background: uploading ? "#9ca3af" : "#2563eb",
          color: "white",
          borderRadius: 6,
          cursor: uploading ? "default" : "pointer",
        }}
      >
        {uploading ? "업로드 중..." : "PDF 업로드"}
        <input
          type="file"
          accept="application/pdf"
          onChange={handleUpload}
          disabled={uploading}
          style={{ display: "none" }}
        />
      </label>

      {error && (
        <div style={{ color: "#dc2626", marginTop: 12, whiteSpace: "pre-wrap" }}>{error}</div>
      )}

      <table style={{ width: "100%", marginTop: 24, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "2px solid #e5e7eb" }}>
            <th style={{ padding: 8 }}>파일명</th>
            <th style={{ padding: 8 }}>상태</th>
            <th style={{ padding: 8 }}>페이지</th>
            <th style={{ padding: 8 }}>제목</th>
            <th style={{ padding: 8 }}>작성자</th>
          </tr>
        </thead>
        <tbody>
          {documents.length === 0 && (
            <tr>
              <td colSpan={5} style={{ padding: 16, color: "#9ca3af" }}>
                아직 문서가 없다.
              </td>
            </tr>
          )}
          {documents.map((d) => (
            <tr key={d.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
              <td style={{ padding: 8 }}>{d.filename}</td>
              <td style={{ padding: 8 }}>
                <span style={{ color: STATUS_COLOR[d.status] || "#000", fontWeight: 600 }}>
                  {d.status}
                </span>
                {d.status === "FAILED" && d.error && (
                  <div style={{ fontSize: 12, color: "#dc2626" }}>{d.error}</div>
                )}
              </td>
              <td style={{ padding: 8 }}>{d.page_count ?? "-"}</td>
              <td style={{ padding: 8 }}>{d.title ?? "-"}</td>
              <td style={{ padding: 8 }}>{d.author ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
