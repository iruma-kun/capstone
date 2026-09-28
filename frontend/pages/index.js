import React, { useState, useEffect } from "react";
import {
  FileText,
  Shield,
  AlertTriangle,
  CheckCircle,
  Search,
  Upload,
  Cloud,
  Activity,
  Download,
  FileWarning,
  Info,
  ExternalLink,
} from "lucide-react";

export default function ComplianceDashboard() {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const API_BASE = "http://localhost:8000/api";

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/documents`);
      if (!res.ok) throw new Error("Failed to fetch documents");
      const data = await res.json();
      setDocuments(data);
    } catch (err) {
      console.warn("Backend offline, using fallback data.");
      setDocuments([
        {
          id: 1,
          filename: "Q3_Financial_Report.txt",
          category: "Financial",
          upload_date: "2026-09-28 10:15:00",
          status: "Completed",
          risk_score: 7.2,
          report: {
            compliance_rating: "Fail",
            summary: "Critical issues detected in auditor disclosures.",
          },
          findings: [
            {
              id: 101,
              category: "Finance",
              risk_level: "High",
              title: "Missing Independent Auditor",
              description: "No auditor sign-off detected.",
              evidence_excerpt: "...prepared by internal team...",
              confidence_score: 0.92,
            },
          ],
        },
        {
          id: 2,
          filename: "Sustainability_2026.txt",
          category: "ESG",
          upload_date: "2026-09-28 09:45:00",
          status: "Completed",
          risk_score: 4.5,
          report: {
            compliance_rating: "Conditional",
            summary: "Vague net-zero claims without Scope 3 metrics.",
          },
          findings: [
            {
              id: 102,
              category: "ESG",
              risk_level: "Medium",
              title: "Unverified Net-Zero",
              description: "Missing scope 3 data.",
              evidence_excerpt: "...commit to net-zero by 2040...",
              confidence_score: 0.85,
            },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const seedSamples = async () => {
    try {
      await fetch(`${API_BASE}/seed-samples`, { method: "POST" });
      setSuccess("Sample documents seeded into the audit engine.");
      fetchDocuments();
    } catch (err) {
      setError("Could not connect to backend to seed samples.");
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const getRiskColor = (score) => {
    if (score >= 7) return "text-rose-400 border-rose-500/50 bg-rose-500/10";
    if (score >= 4) return "text-amber-400 border-amber-500/50 bg-amber-500/10";
    return "text-emerald-400 border-emerald-500/50 bg-emerald-500/10";
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-200 p-6 lg:p-10 font-sans">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 pb-6 border-b border-slate-800 gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-indigo-500 p-2 rounded-lg shadow-[0_0_15px_rgba(99,102,241,0.5)]">
              <Shield className="text-white w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Compliance<span className="text-indigo-400">Audit</span>.ai
            </h1>
          </div>
          <p className="text-slate-400 text-sm">
            Automated Regulatory Risk Intelligence & Document Auditing
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={seedSamples}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded-lg text-sm transition border border-slate-700"
          >
            <Activity className="w-4 h-4 text-indigo-400" /> Seed Samples
          </button>
          <button
            onClick={fetchDocuments}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2 rounded-lg text-sm font-semibold shadow-lg shadow-indigo-500/20 transition"
          >
            <Upload className="w-4 h-4" /> Upload Document
          </button>
        </div>
      </header>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        {[
          {
            label: "Documents Audited",
            value: documents.length,
            icon: FileText,
            color: "text-indigo-400",
          },
          {
            label: "Critical Risks",
            value: documents.filter((d) => d.risk_score >= 7).length,
            icon: AlertTriangle,
            color: "text-rose-400",
          },
          {
            label: "Pending Review",
            value: 0,
            icon: Activity,
            color: "text-amber-400",
          },
          {
            label: "Cloud Status",
            value: "Operational",
            icon: Cloud,
            color: "text-emerald-400",
          },
        ].map((stat, i) => (
          <div
            key={i}
            className="bg-slate-800/50 border border-slate-700/50 p-5 rounded-2xl"
          >
            <div className="flex justify-between items-start mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {stat.label}
              </span>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div className="text-2xl font-bold text-white">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Document List */}
        <div className="lg:col-span-4 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
            <Search className="w-4 h-4 text-slate-400" /> Recent Audits
          </h2>
          <div className="space-y-3 overflow-y-auto max-h-[600px] pr-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => setSelectedDoc(doc)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  selectedDoc?.id === doc.id
                    ? "bg-indigo-500/10 border-indigo-500/50"
                    : "bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/60"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-semibold text-sm truncate max-w-[180px]">
                    {doc.filename}
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRiskColor(doc.risk_score)}`}
                  >
                    RISK: {doc.risk_score}
                  </span>
                </div>
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>{doc.category} Audit</span>
                  <span>{doc.upload_date.split(" ")[0]}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Audit Report Detail */}
        <div className="lg:col-span-8">
          {selectedDoc ? (
            <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 lg:p-8 animate-in fade-in slide-in-from-right-4 duration-300">
              {/* Report Header */}
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-1">
                    {selectedDoc.filename}
                  </h2>
                  <p className="text-slate-400 text-sm">
                    System ID: COMP-2026-
                    {selectedDoc.id.toString().padStart(4, "0")}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-4 py-1.5 rounded-full text-xs font-bold border ${
                      selectedDoc.report?.compliance_rating === "Pass"
                        ? "bg-emerald-500/10 border-emerald-500/50 text-emerald-400"
                        : selectedDoc.report?.compliance_rating === "Fail"
                          ? "bg-rose-500/10 border-rose-500/50 text-rose-400"
                          : "bg-amber-500/10 border-amber-500/50 text-amber-400"
                    }`}
                  >
                    STATUS: {selectedDoc.report?.compliance_rating || "N/A"}
                  </span>
                  <button className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition text-slate-300">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Executive Summary */}
              <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-5 mb-8">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Info className="w-3.5 h-3.5" /> Executive Summary
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  {selectedDoc.report?.summary ||
                    "No summary available for this document."}
                </p>
              </div>

              {/* Findings */}
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                <FileWarning className="w-4 h-4 text-rose-400" /> Compliance
                Findings ({selectedDoc.findings.length})
              </h3>

              <div className="space-y-4">
                {selectedDoc.findings.map((finding) => (
                  <div
                    key={finding.id}
                    className="bg-slate-800/60 border-l-4 border-l-rose-500 border border-slate-700/50 rounded-r-xl p-5"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="text-[10px] font-bold text-rose-400 uppercase">
                          {finding.risk_level} SEVERITY
                        </span>
                        <h4 className="text-white font-bold">
                          {finding.title}
                        </h4>
                      </div>
                      <span className="text-[10px] bg-slate-700 px-2 py-1 rounded text-slate-300 font-mono">
                        Rule: {finding.rule_id}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 mb-4">
                      {finding.description}
                    </p>

                    <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800/50">
                      <div className="text-[10px] font-bold text-indigo-400 uppercase mb-2 flex items-center gap-1">
                        <Activity className="w-3 h-3" /> Audit Evidence Excerpt
                        (Confidence:{" "}
                        {(finding.confidence_score * 100).toFixed(0)}%)
                      </div>
                      <p className="text-xs text-slate-300 font-mono leading-relaxed italic">
                        "{finding.evidence_excerpt}"
                      </p>
                    </div>
                  </div>
                ))}
                {selectedDoc.findings.length === 0 && (
                  <div className="text-center py-10 bg-slate-900/30 rounded-xl border border-dashed border-slate-700/50">
                    <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    <p className="text-slate-400 text-sm">
                      No compliance risks detected in this document.
                    </p>
                  </div>
                )}
              </div>

              {/* Raw Content Preview */}
              <div className="mt-10 pt-10 border-t border-slate-800">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">
                  Document Content Preview
                </h3>
                <div className="bg-slate-950/50 p-6 rounded-xl border border-slate-800/50 text-xs text-slate-500 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {selectedDoc.content_preview}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center bg-slate-800/20 border border-dashed border-slate-700/50 rounded-2xl">
              <FileText className="w-12 h-12 text-slate-700 mb-4" />
              <p className="text-slate-500 font-medium text-center max-w-xs">
                Select a document from the audit queue to view detailed
                compliance analysis and risk findings.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
