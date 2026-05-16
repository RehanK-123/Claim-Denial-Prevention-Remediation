import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { Amplify } from "aws-amplify";
import { fetchAuthSession, signOut, getCurrentUser } from "aws-amplify/auth";
import "@aws-amplify/ui-react/styles.css";
import {
  AlertCircle,
  CheckCircle,
  FileText,
  ArrowLeft,
  Zap,
  HelpCircle,
  ListOrdered,
  ShieldCheck,
  LogOut,
  Lock,
  Activity, 
  ShieldAlert, 
  Wrench,
  ChevronRight
} from "lucide-react";

/* =========================================================
   AWS COGNITO CONFIGURATION
   ========================================================= */
const RECTIFIED_DOMAIN = "us-east-1zstxe2bwo.auth.us-east-1.amazoncognito.com"; 
const CLIENT_ID = "4n9rrc9o53vjng827bvdhrlvdh";

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: "us-east-1_zSTxe2BWO",
      userPoolClientId: CLIENT_ID,
      loginWith: {
        oauth: {
          domain: RECTIFIED_DOMAIN,
          scopes: ["email", "openid", "phone"],
          redirectSignIn: ["http://localhost:5173/input"],
          redirectSignOut: ["http://localhost:5173"],
          responseType: "code",
        },
      },
    },
  },
});

/* =========================================================
   LOGIN PAGE
   ========================================================= */
function LoginPage() {
  const [loading, setLoading] = useState(false);

  const handleLoginClick = () => {
    setLoading(true);
    const loginUrl =
      `https://${RECTIFIED_DOMAIN}/login?` +
      `client_id=${CLIENT_ID}&` +
      `response_type=code&` +
      `scope=email+openid+phone&` +
      `redirect_uri=${encodeURIComponent("http://localhost:5173/input")}`;

    window.location.assign(loginUrl);
  };

  const handleSignupClick = () => {
    setLoading(true);
    const signupUrl =
      `https://${RECTIFIED_DOMAIN}/signup?` +
      `client_id=${CLIENT_ID}&` +
      `response_type=code&` +
      `scope=email+openid+phone&` +
      `redirect_uri=${encodeURIComponent("http://localhost:5173/input")}`;

    window.location.assign(signupUrl);
  };

  return (<div className="min-h-screen flex flex-col items-center justify-center bg-[#F8FAFC] p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-10">
          <div className="inline-flex p-3.5 bg-indigo-600 rounded-2xl mb-6 shadow-lg shadow-indigo-200">
            <ShieldCheck className="h-7 w-7 text-white" />
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-600 tracking-wider uppercase">
            Auditing Tool
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-2 mb-3">
            CeDAR
          </h1>
          <p className="text-sm text-slate-500 font-medium">
            Claim Evaluation, Denial Assessment and Remediation
          </p>
        </div>

        <div className="bg-white border border-slate-200 shadow-sm rounded-3xl p-8 space-y-6">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Access Portal</h2>
            <p className="text-xs text-slate-500 font-medium">
              Sign in with your Cognito credentials to access the claims platform
            </p>
          </div>

          <button
            onClick={handleLoginClick}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3.5 px-6 rounded-xl hover:bg-indigo-700 active:scale-[0.99] transition-all shadow-sm text-sm disabled:opacity-50"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Lock className="h-4 w-4" />
            )}
            Sign In to Account
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-white text-slate-500 font-medium">New User?</span>
            </div>
          </div>

          <button
            onClick={handleSignupClick}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 border border-slate-200 bg-white text-slate-700 font-semibold py-3.5 px-6 rounded-xl hover:bg-slate-50 active:scale-[0.99] transition-all text-sm shadow-sm disabled:opacity-50"
          >
            Create Account
          </button>

          <p className="text-center text-[10px] text-slate-400 font-medium uppercase tracking-wider">
            AWS Cognito Managed Authentication
          </p>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   MAIN CLAIM APPLICATION
   ========================================================= */
function ClaimDenialFrontend() {
  const [claim, setClaim] = useState({
    claim_id: "CLM-90821",
    patient_id: "PT-7721",
    provider_id: "PROV-440",
    diagnosis_code: "M54.50",
    procedure_code: "99214",
    billed_amount: "450.00",
    date: "2026-05-14"
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [predictionData, setPredictionData] = useState(null);
  const [currentPage, setCurrentPage] = useState("form");
  const [activeTab, setActiveTab] = useState("overview");

  const pastelColors = {
    bg: "bg-[#F8FAFC]",
    card: "bg-white border border-[#E2E8F0] shadow-sm rounded-3xl",
    textMain: "text-[#334155]",
    textDark: "text-[#0F172A]"
  };

  // Structured Text Parser for Markdown Knowledge Base Chunks
  const parseChunkText = (text) => {
    if (!text || typeof text !== 'string') return { rootCause: "", signals: [], steps: [], strategy: [] };
    
    const sanitized = text.split("================================================================================")[0];
    const lines = sanitized.split("\n").map(l => l.trim()).filter(Boolean);
    let currentSection = "";
    
    const data = { rootCause: "", signals: [], steps: [], strategy: [] };

    lines.forEach(line => {
      if (line.toUpperCase().includes("ROOT CAUSE:")) {
        currentSection = "root";
        return;
      }
      if (line.toUpperCase().includes("DETECTION SIGNALS:")) {
        currentSection = "signals";
        return;
      }
      if (line.toUpperCase().includes("REMEDIATION STEPS:")) {
        currentSection = "steps";
        return;
      }
      if (line.toUpperCase().includes("PREVENTION STRATEGY:")) {
        currentSection = "strategy";
        return;
      }
      if (line.toUpperCase().includes("VALIDATION CHECKS:") || line.toUpperCase().includes("ESCALATION CONDITIONS:")) {
        currentSection = "skip";
        return;
      }

      const cleanLine = line.replace(/^[*-\d.]\s*/, ""); 
      if (currentSection === "root") data.rootCause += (data.rootCause ? " " : "") + line;
      if (currentSection === "signals") data.signals.push(cleanLine);
      if (currentSection === "steps") data.steps.push(cleanLine);
      if (currentSection === "strategy") data.strategy.push(cleanLine);
    });

    return data;
  };

  const handleChange = (e) => {
    setClaim({ ...claim, [e.target.name]: e.target.value });
  };

  const [llmSummary, setLlmSummary] = useState("");
  const validateAndPredictClaim = async () => {
    setLoading(true);
    setError("");
    
    const payload = {
      ...claim,
      billed_amount: parseFloat(claim.billed_amount) || 0.0
    };

    try {
      // Step 1: Format Checks Routing
      const validateResponse = await fetch("http://127.0.0.1:8000/validate-claim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!validateResponse.ok) {
        throw new Error(`Validation failed with server status: ${validateResponse.status}`);
      }
      
      const validationResult = await validateResponse.json();

      if (validationResult.status !== "SUCCESS") {
        setError(validationResult.message || "Claim validation failed format checks.");
        setLoading(false);
        return;
      }

      // Step 2: Risk Scoring Matrix Mapping Pipeline
      const predictResponse = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!predictResponse.ok) {
        throw new Error(`Prediction engine failed with server status: ${predictResponse.status}`);
      }

      const predictionResult = await predictResponse.json();

      if (predictionResult.status !== "SUCCESS") {
        setError(predictionResult.message || "Prediction generation failure.");
        setLoading(false);
        return;
      }

      setPredictionData(predictionResult);
      setCurrentPage("prediction");
      setActiveTab("overview");

    } catch (err) {
      setError(`Network Pipeline Failure: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderInput = (label, name, type = "text") => (
    <div className="flex flex-col gap-2 text-left">
      <label className="text-xs font-semibold tracking-wide uppercase text-slate-500">
        {label}
      </label>
      <input
        type={type}
        name={name}
        value={claim[name]}
        onChange={handleChange}
        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 outline-none transition-all focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50/50 text-sm"
        placeholder={label}
      />
    </div>
  );

  return (
    <div className={`min-h-screen ${pastelColors.bg} py-12 px-4 sm:px-6 lg:px-8 font-sans ${pastelColors.textMain}`}>
      <div className="max-w-4xl mx-auto">
        
        {/* Title Area */}
        <div className="mb-10 text-center">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-600 tracking-wider uppercase">
            Auditing Tool
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-2 mb-3">
            CeDAR: Claim Evaluation, Denial Assessment and Remediation
          </h1>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2 text-left">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* INPUT STAGE PANEL */}
        {currentPage === "form" && (
          <div className={pastelColors.card}>
            <div className="border-b border-slate-100 p-6 text-left">
              <h2 className="text-lg font-bold text-slate-900">Claim Parameters</h2>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {renderInput("Claim ID Reference", "claim_id")}
                {renderInput("Patient ID Reference", "patient_id")}
                {renderInput("Provider NPI Code", "provider_id")}
                {renderInput("ICD-10 Diagnosis Vector", "diagnosis_code")}
                {renderInput("CPT Operational Code", "procedure_code")}
                {renderInput("Billed Amount ($)", "billed_amount", "number")}
                <div className="md:col-span-2">{renderInput("Timeline Date", "date", "date")}</div>
              </div>

              <button
                onClick={validateAndPredictClaim}
                disabled={loading}
                className="w-full mt-2 bg-indigo-600 text-white rounded-xl py-3.5 px-4 font-semibold text-sm hover:bg-indigo-700 active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
              >
                {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Verify and Predict Outcome"}
              </button>
            </div>
          </div>
        )}

        {/* OUTPUT STAGE DASHBOARD */}
        {currentPage === "prediction" && predictionData && (
          <div className="space-y-6 animate-fade-in text-left">
            <button onClick={() => setCurrentPage("form")} className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm">
              <ArrowLeft className="w-3.5 h-3.5" /> Return to Form
            </button>

            {/* Formal Decision Verdict Banner Container */}
            <div className={`rounded-3xl p-6 shadow-sm border text-slate-800 transition-all ${
              predictionData.prediction === 0 
                ? "bg-[#F0FDF4] border-emerald-200 shadow-emerald-500/5" 
                : "bg-[#FFF1F2] border-rose-200 shadow-rose-500/5"
            }`}>
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                <div className="flex items-start gap-4">
                  <div className={`p-3.5 rounded-2xl shrink-0 ${predictionData.prediction === 0 ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
                    {predictionData.prediction === 0 ? <CheckCircle className="w-6 h-6" /> : <AlertCircle className="w-6 h-6" />}
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold tracking-widest uppercase opacity-60">Automated Adjudication Analysis</span>
                    {predictionData.prediction === 0 ? (
                      <div>
                        <h2 className="text-xl font-extrabold tracking-tight text-emerald-950">CLAIM COMPLIANCE CLEARED</h2>
                        <p className="text-xs text-emerald-800/80 font-medium leading-relaxed mt-1">Transaction matches institutional parameter limits. Automated approval protocol initialized with baseline operational safety markers.</p>
                      </div>
                    ) : (
                      <div>
                        <h2 className="text-xl font-extrabold tracking-tight text-rose-950">ELEVATED DENIAL RISK IDENTIFIED</h2>
                        <p className="text-xs text-rose-800/80 font-medium leading-relaxed mt-1">Transaction flags policy exceptions. Routine automated adjudication suspended. Compliance intervention recommended.</p>
                      </div>
                    )}
                  </div>
                </div>
                {predictionData.probability !== undefined && (
                  <div className="bg-white/70 backdrop-blur-sm px-4 py-2.5 rounded-2xl border border-white/50 min-w-[120px] flex sm:flex-col justify-between items-center sm:items-end self-stretch sm:self-auto">
                    <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">{predictionData.prediction === 0 ? "Safety Score" : "Risk Probability"}</p>
                    <p className={`text-2xl font-black font-mono tracking-tight ${predictionData.prediction === 0 ? "text-emerald-700" : "text-rose-700"}`}>{(predictionData.probability * 100).toFixed(0)}%</p>
                  </div>
                )}
              </div>
            </div>

            {/* Explanations Drivers Component */}
            <div className={pastelColors.card + " p-6"}>
              <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2"><Zap className="w-4 h-4 text-amber-500 fill-amber-500" />Primary Drivers of Variance</h3>
              <div className="space-y-3">
                {predictionData.explanations && predictionData.explanations.length > 0 ? (
                  predictionData.explanations.map((exp, idx) => (
                    <div key={idx} className="flex gap-3 rounded-xl bg-[#FFF9F2] p-4 border border-[#FEEFDD]">
                      <div className="w-1 bg-[#FDBA74] rounded-full flex-shrink-0" />
                      <p className="text-xs font-medium text-slate-700">{exp}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 italic">No variance indicators flagged.</p>
                )}
              </div>
            </div>

            {/* TABS CONTROL MATRIX SELECTOR */}
            <div className="bg-slate-200/50 p-1 rounded-2xl flex gap-1 shadow-inner">
              {["overview", "remediations", "policies"].map((t) => (
                <button key={t} onClick={() => setActiveTab(t)} className={`flex-1 py-3 rounded-xl text-xs font-bold capitalize transition-all ${activeTab === t ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500"}`}>
                  {t === "overview" ? "Cost Comparison" : t}
                </button>
              ))}
            </div>

            {/* TAB PANEL CONTENTS DISPLAY WRAPPER */}
            <div className={pastelColors.card + " p-6"}>
              
              {/* PANEL A: FINANCIAL SPECTRUM METRICS */}
              {activeTab === "overview" && predictionData.transformed_claim && (
                <div className="space-y-6 animate-fade-in">
                  <div className="space-y-4">
                    {[
                      { label: "Gross Billed Value", val: predictionData.transformed_claim.billed_amount, bg: "bg-[#FCE7F3]" },
                      { label: "Statutory Model Target", val: predictionData.transformed_claim.expected_cost, bg: "bg-[#E0F2FE]" },
                      { label: "Procedure Core Median", val: predictionData.transformed_claim.average_cost, bg: "bg-[#DCFCE7]" },
                    ].map((item, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold">
                          <span>{item.label}</span>
                          <span className="font-mono font-bold">${Number(item.val || 0).toFixed(2)}</span>
                        </div>
                        <div className="h-7 w-full rounded-xl bg-slate-100 overflow-hidden">
                          <div className={`h-full ${item.bg} rounded-xl`} style={{ width: `${Math.min((item.val / (predictionData.transformed_claim.billed_amount || 1)) * 100, 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* PANEL B: DYNAMIC SPLIT REMEDIATIONS DATA GRID */}
              {activeTab === "remediations" && (
                <div className="space-y-6 animate-fade-in">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">Recommended Remediations Pipeline</h4>
                    <p className="text-xs text-slate-400 mt-0.5">Iterative structural modifications generated algorithmically from active knowledge nodes.</p>
                  </div>

                  <div className="space-y-6">
                    {predictionData.recommended_remediation && predictionData.recommended_remediation.length > 0 ? (
                      predictionData.recommended_remediation.map((item, idx) => {
                        const parsed = parseChunkText(item.chunk_text);
                        return (
                          <div key={idx} className="p-5 border border-slate-100 rounded-2xl bg-slate-50/50 space-y-4 shadow-sm">
                            <div className="flex flex-wrap justify-between items-center gap-2 border-b border-slate-100 pb-3">
                              <div className="flex items-center gap-2">
                                <span className="px-2.5 py-1 font-mono text-xs font-bold bg-[#E9E3F8] text-purple-800 rounded-md">{item.fix_id}</span>
                                <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">UUID: {item.chunk_id}</span>
                              </div>
                              {item.score && (
                                <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">
                                  Match Score: {(item.score * 100).toFixed(1)}%
                                </span>
                              )}
                            </div>

                            {parsed.rootCause && (
                              <div className="text-xs bg-amber-50/60 p-3 rounded-xl border border-amber-100/50">
                                <span className="font-bold text-amber-800 block mb-0.5">Root Cause Variance:</span>
                                <p className="text-slate-600 font-medium leading-relaxed">{parsed.rootCause}</p>
                              </div>
                            )}

                            {parsed.signals.length > 0 && (
                              <div className="space-y-1">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1"><HelpCircle className="w-3 h-3"/> Detection Signals</span>
                                <div className="flex flex-wrap gap-1.5">
                                  {parsed.signals.map((sig, sIdx) => (
                                    <span key={sIdx} className="text-[11px] font-medium bg-[#E0F2FE] text-blue-800 px-2 py-0.5 rounded-md">{sig}</span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {parsed.steps.length > 0 && (
                              <div className="space-y-2">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1"><ListOrdered className="w-3 h-3"/> Ordered Correction Sequence</span>
                                <div className="grid grid-cols-1 gap-2">
                                  {parsed.steps.map((step, sIdx) => (
                                    <div key={sIdx} className="flex gap-2.5 bg-white p-2.5 rounded-xl border border-slate-100 text-xs text-slate-700">
                                      <span className="font-bold text-indigo-500 font-mono">{sIdx + 1}.</span>
                                      <p className="font-medium">{step}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {parsed.strategy.length > 0 && (
                              <div className="text-[11px] bg-emerald-50/40 p-2.5 rounded-xl border border-emerald-100/50 text-slate-600 flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0"/>
                                <p><strong>Prevention Model Strategy:</strong> {parsed.strategy.join(" ")}</p>
                              </div>
                            )}
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-xs text-slate-400 italic">No remediation structures returned.</p>
                    )}
                  </div>
                </div>
              )}

              {/* PANEL C: RELEVANT INSURANCE CONTRACT POLICIES */}
              {activeTab === "policies" && (
                <div className="space-y-4 animate-fade-in">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">Referenced Insurance Policies</h4>
                    <p className="text-xs text-slate-400 mt-0.5">Contract documentation nodes linked directly to current validation telemetry patterns.</p>
                  </div>

                  <div className="space-y-3">
                    {predictionData.relevant_policies && predictionData.relevant_policies.length > 0 ? (
                      predictionData.relevant_policies.map((policy, idx) => (
                        <div key={idx} className="p-4 rounded-2xl border border-slate-100 bg-white hover:bg-slate-50 transition-colors flex flex-col gap-2.5 shadow-sm">
                          <div className="flex justify-between items-start gap-4">
                            <div className="flex items-center gap-3">
                              <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600"><FileText className="w-4 h-4" /></div>
                              <div>
                                <p className="text-xs font-bold text-slate-800">Policy Reference Node</p>
                                <p className="text-[10px] font-mono text-slate-400 mt-0.5">ID: {policy.policy_id} | Chunk: {policy.chunk_id}</p>
                              </div>
                            </div>
                            {policy.score && (
                              <span className="text-[10px] font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-100">
                                Relevance: {(policy.score * 100).toFixed(1)}%
                              </span>
                            )}
                          </div>
                          <div className="text-xs bg-slate-50 p-3 rounded-xl border border-slate-100 text-slate-600 font-medium leading-relaxed italic">
                            "{policy.chunk_text}"
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-400 italic">No insurance policies matched to this telemetry vector map.</p>
                    )}
                  </div>
                </div>
              )}

            </div>
          </div>
        )}

      </div>
    </div>
  );
}


/* =========================================================
   EXPORTED ROOT COMPONENT
   ========================================================= */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/input" element={<ClaimDenialFrontend />} />
        <Route path="*" element={<ClaimDenialFrontend />} />
      </Routes>
    </BrowserRouter>
  );
}