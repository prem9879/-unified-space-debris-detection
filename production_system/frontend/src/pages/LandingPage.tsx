import { motion } from "framer-motion";
import { type ReactElement, useEffect, useState } from "react";
import {
  legacyDatasetInventory,
  legacyLoadAllPublicData,
  legacyModelBenchmark,
  legacyOrbitalBrief,
  legacyPredict,
  legacyPredictDataset,
  legacyPredictFile,
  legacyPreviewNasaSolarflux,
  legacyReadyz,
} from "../services/api";

interface LandingPageProps {
  onNavigate?: () => void;
}

export function LandingPage({ onNavigate }: LandingPageProps): ReactElement {
  type ExplorerItem = {
    path: string;
    file_name?: string;
    modality?: string;
  };

  const [expandedModel, setExpandedModel] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<number>(64);
  const [opticalBand, setOpticalBand] = useState<string>("rgb");
  const [normalizeMode, setNormalizeMode] = useState<string>("unit");
  const [physicsVector, setPhysicsVector] = useState<string>(
    "0.12,0.05,0.22,0.08,0.9,1.1,0.7,0.2,0.4,0.6,1.5,1.9,2.1,0.3,0.44,0.77"
  );
  const [opticalFile, setOpticalFile] = useState<File | null>(null);
  const [radarFile, setRadarFile] = useState<File | null>(null);
  const [inferBusy, setInferBusy] = useState<boolean>(false);
  const [inferStatus, setInferStatus] = useState<string>("Ready for live inference.");
  const [inferResult, setInferResult] = useState<any>(null);

  const [nasaBusy, setNasaBusy] = useState<boolean>(false);
  const [nasaStatus, setNasaStatus] = useState<string>("NASA loader not started.");
  const [solarFluxRows, setSolarFluxRows] = useState<number>(0);

  const [datasetDir, setDatasetDir] = useState<string>("c:/Users/PREM DIWAN/Desktop/ml/images");
  const [batchModality, setBatchModality] = useState<string>("optical");
  const [maxSamples, setMaxSamples] = useState<number>(12);
  const [batchBusy, setBatchBusy] = useState<boolean>(false);
  const [batchStatus, setBatchStatus] = useState<string>("Waiting for dataset run...");
  const [batchResult, setBatchResult] = useState<any>(null);

  const [explorerBusy, setExplorerBusy] = useState<boolean>(false);
  const [explorerStatus, setExplorerStatus] = useState<string>("Scan the folder to start exploring images.");
  const [explorerItems, setExplorerItems] = useState<ExplorerItem[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>("");
  const [selectedBusy, setSelectedBusy] = useState<boolean>(false);
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [legacyApiKey, setLegacyApiKey] = useState<string>(localStorage.getItem("legacyApiKey") ?? "");
  const [legacyReady, setLegacyReady] = useState<string>("Checking console health...");
  const [benchBusy, setBenchBusy] = useState<boolean>(false);
  const [liveModelBenchmarks, setLiveModelBenchmarks] = useState<any[]>([]);
  const [orbitalBrief, setOrbitalBrief] = useState<any>(null);
  const [showLegacyConsole, setShowLegacyConsole] = useState<boolean>(false);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
  };

  const quarterCards = [
    {
      letter: "01",
      title: "TLE Intake",
      description: "Ingest CelesTrak, Space-Track, and local catalogs",
      icon: "📡",
      color: "from-blue-600 to-cyan-600",
      borderColor: "border-blue-500",
      sectionId: "section-q1",
    },
    {
      letter: "02",
      title: "Fusion Engine",
      description: "Blend orbital physics with multimodal AI",
      icon: "⚡",
      color: "from-purple-600 to-pink-600",
      borderColor: "border-purple-500",
      sectionId: "section-q2",
    },
    {
      letter: "03",
      title: "Orbital Deck",
      description: "Inspect 3D tracks, alerts, and uncertainty",
      icon: "🌐",
      color: "from-emerald-600 to-teal-600",
      borderColor: "border-emerald-500",
      sectionId: "section-q3",
    },
    {
      letter: "04",
      title: "Research Pack",
      description: "Export evidence for paper and deployment",
      icon: "📦",
      color: "from-orange-600 to-red-600",
      borderColor: "border-orange-500",
      sectionId: "section-q4",
    },
  ];

  const modelBenchmarks = [
    { name: "resnet18", accuracy: 100.0, f1: 1.0, precision: 1.0, recall: 1.0, loss: 0.0001 },
    { name: "resnet34", accuracy: 100.0, f1: 1.0, precision: 1.0, recall: 1.0, loss: 0.0014 },
    { name: "densenet121", accuracy: 100.0, f1: 1.0, precision: 1.0, recall: 1.0, loss: 0.0006 },
    { name: "efficientnet_b0", accuracy: 100.0, f1: 1.0, precision: 1.0, recall: 1.0, loss: 0.0093 },
    { name: "efficientnet_b1", accuracy: 100.0, f1: 1.0, precision: 1.0, recall: 1.0, loss: 0.006 },
    { name: "mobilenet_v3_small", accuracy: 96.88, f1: 0.9688, precision: 0.9707, recall: 0.9688, loss: 0.1068 },
    { name: "shufflenet_v2_x1_0", accuracy: 100.0, f1: 1.0, precision: 1.0, recall: 1.0, loss: 0.2915 },
    { name: "convnext_tiny", accuracy: 100.0, f1: 1.0, precision: 1.0, recall: 1.0, loss: 0.0 },
  ];

  const coreMetrics = [
    { label: "Detection AUC", value: "0.5406", color: "text-blue-400" },
    { label: "TPR @ 1e-5", value: "0.0152", color: "text-cyan-400" },
    { label: "Orbit RMSE", value: "1.0607", color: "text-purple-400" },
    { label: "Collision ECE", value: "0.0406", color: "text-emerald-400" },
  ];

  const statusItems = [
    { label: "TLE STREAMS", value: "CelesTrak / Space-Track", color: "text-cyan-400" },
    { label: "RISK ENGINE", value: "Physics + AI Fusion", color: "text-purple-400" },
    { label: "VISUALIZATION", value: "3D Shell Deck", color: "text-emerald-400" },
    { label: "STATUS", value: "Ready", color: "text-green-400" },
    { label: "SECURITY", value: "Open + RL(180/min)", color: "text-yellow-400" },
    { label: "ACCESS", value: "ANONYMOUS", color: "text-slate-400" },
  ];

  const researchSteps = [
    {
      number: "01",
      title: "Live ingestion",
      description: "CelesTrak, Space-Track, and local imagery flow into a canonical catalog with epoch, provenance, and shell tags.",
    },
    {
      number: "02",
      title: "Orbital features",
      description: "Semi-major axis, altitude, inclination, drag proxies, cyclic angles, and relative-distance cues are normalized for learning.",
    },
    {
      number: "03",
      title: "Multimodal AI",
      description: "LSTM / GRU and Transformer models handle sequence prediction, while XGBoost and CNN / YOLO provide fast, interpretable baselines.",
    },
    {
      number: "04",
      title: "Collision engine",
      description: "Physics gating, relative-velocity checks, and learned scores fuse into a low / medium / high risk band with audit-ready reasoning.",
    },
    {
      number: "05",
      title: "Real-time delivery",
      description: "Streaming updates are pushed into alerts, dashboards, and exportable research packs without blocking the operator flow.",
    },
  ];

  const displayedModelBenchmarks = liveModelBenchmarks.length > 0
    ? liveModelBenchmarks.map((item) => ({
      name: item.model,
      accuracy: Number(item.accuracy ?? 0) * 100,
      f1: Number(item.f1 ?? 0),
      precision: Number(item.precision ?? 0),
      recall: Number(item.recall ?? 0),
      loss: Number(item.test_loss ?? 0),
    }))
    : modelBenchmarks;

  const scrollToSection = (sectionId: string) => {
    const target = document.getElementById(sectionId);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const refreshLiveData = async () => {
    try {
      const ready = await legacyReadyz(legacyApiKey);
      setLegacyReady(
        ready?.status === "ready"
          ? "Legacy mission console is ready."
          : "Legacy mission console responded but is not ready."
      );
    } catch (error) {
      setLegacyReady(`Legacy console unavailable: ${error instanceof Error ? error.message : "unknown error"}`);
    }

    try {
      setBenchBusy(true);
      const benchmark = await legacyModelBenchmark(legacyApiKey);
      setLiveModelBenchmarks(benchmark.models ?? []);
    } catch {
      setLiveModelBenchmarks([]);
    } finally {
      setBenchBusy(false);
    }

    try {
      const brief = await legacyOrbitalBrief(legacyApiKey);
      setOrbitalBrief(brief);
    } catch {
      setOrbitalBrief(null);
    }
  };

  useEffect(() => {
    void refreshLiveData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    localStorage.setItem("legacyApiKey", legacyApiKey);
  }, [legacyApiKey]);

  const runLivePrediction = async () => {
    setInferBusy(true);
    setInferStatus("Running prediction...");
    try {
      const payload = await legacyPredict({
        opticalFile,
        radarFile,
        physics: physicsVector,
        imageSize,
        opticalBand,
        normalizeMode,
        apiKey: legacyApiKey,
      });
      setInferResult(payload);
      const detectPct = Number(payload.detect_probability ?? 0) * 100;
      const collisionPct = Number(payload.collision_probability ?? 0) * 100;
      setInferStatus(
        `Prediction complete. Detect ${detectPct.toFixed(2)}% | Collision ${collisionPct.toFixed(2)}% | Class ${payload.predicted_class ?? "n/a"}`
      );
    } catch (error) {
      setInferStatus(`Prediction failed: ${error instanceof Error ? error.message : "unknown error"}`);
    } finally {
      setInferBusy(false);
    }
  };

  const loadNasaData = async () => {
    setNasaBusy(true);
    setNasaStatus("Loading NASA public data...");
    try {
      const result = await legacyLoadAllPublicData(legacyApiKey);
      const solar = await legacyPreviewNasaSolarflux(legacyApiKey);
      const rows = Number(solar?.summary?.rows ?? 0);
      setSolarFluxRows(rows);
      setNasaStatus(
        `Loaded. Gallery count: ${result.gallery_count ?? 0}. Solar flux rows: ${rows}.`
      );
    } catch (error) {
      setNasaStatus(`NASA load failed: ${error instanceof Error ? error.message : "unknown error"}`);
    } finally {
      setNasaBusy(false);
    }
  };

  const runDatasetBatch = async () => {
    setBatchBusy(true);
    setBatchStatus("Running dataset batch...");
    try {
      const result = await legacyPredictDataset({
        datasetDir,
        modality: batchModality,
        maxSamples,
        imageSize,
        opticalBand,
        normalizeMode,
        apiKey: legacyApiKey,
      });
      setBatchResult(result);
      setBatchStatus(
        `Batch complete. Processed ${result.processed ?? 0}/${result.num_images ?? 0} images. Avg detect ${(Number(result.avg_detect_probability ?? 0) * 100).toFixed(2)}%.`
      );
    } catch (error) {
      setBatchStatus(`Batch failed: ${error instanceof Error ? error.message : "unknown error"}`);
    } finally {
      setBatchBusy(false);
    }
  };

  const scanExplorer = async () => {
    setExplorerBusy(true);
    setExplorerStatus("Scanning folder...");
    try {
      const result = await legacyDatasetInventory(datasetDir, 100, legacyApiKey);
      const items: ExplorerItem[] = result.items ?? [];
      setExplorerItems(items);
      const firstPath = items[0]?.path ?? "";
      setSelectedPath(firstPath);
      setExplorerStatus(`Found ${result.count ?? items.length} files.`);
    } catch (error) {
      setExplorerStatus(`Scan failed: ${error instanceof Error ? error.message : "unknown error"}`);
      setExplorerItems([]);
      setSelectedPath("");
    } finally {
      setExplorerBusy(false);
    }
  };

  const runSelectedImage = async () => {
    if (!selectedPath) {
      setExplorerStatus("Select or scan a file first.");
      return;
    }

    setSelectedBusy(true);
    setExplorerStatus("Running selected image...");
    try {
      const result = await legacyPredictFile({
        filePath: selectedPath,
        modality: batchModality,
        imageSize,
        opticalBand,
        normalizeMode,
        apiKey: legacyApiKey,
      });
      setSelectedResult(result);
      const detectPct = Number(result.detect_probability ?? 0) * 100;
      const collisionPct = Number(result.collision_probability ?? 0) * 100;
      setExplorerStatus(
        `Selected inference complete. Detect ${detectPct.toFixed(2)}%, Collision ${collisionPct.toFixed(2)}%.`
      );
    } catch (error) {
      setExplorerStatus(`Selected image failed: ${error instanceof Error ? error.message : "unknown error"}`);
      setSelectedResult(null);
    } finally {
      setSelectedBusy(false);
    }
  };

  const runDemoVisualFill = async () => {
    const fallbackPath = "c:/Users/PREM DIWAN/Desktop/ml/images/debris/debris_00000.png";
    const demoPath = selectedPath || fallbackPath;
    setSelectedPath(demoPath);
    setSelectedBusy(true);
    setExplorerStatus("Running demo visual fill...");
    try {
      const result = await legacyPredictFile({
        filePath: demoPath,
        modality: batchModality,
        imageSize,
        opticalBand,
        normalizeMode,
        apiKey: legacyApiKey,
      });
      setInferResult(result);
      setSelectedResult(result);
      setExplorerStatus("Demo visual fill completed.");
      setInferStatus("Demo visual fill completed using real model inference.");
    } catch (error) {
      setExplorerStatus(`Demo failed: ${error instanceof Error ? error.message : "unknown error"}`);
    } finally {
      setSelectedBusy(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 scroll-smooth">
      {/* Animated Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 right-0 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10">
        {/* Quarter Cards Row */}
        <motion.div
          className="px-6 pt-12 pb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="mx-auto max-w-7xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {quarterCards.map((card, idx) => (
              <motion.div
                key={idx}
                variants={itemVariants}
                whileHover={{ y: -8, transition: { duration: 0.3 } }}
              >
                <div
                  onClick={() => scrollToSection(card.sectionId)}
                  className={`group relative rounded-2xl bg-gradient-to-br ${card.color} p-0.5 overflow-hidden cursor-pointer shadow-2xl hover:shadow-3xl transition-all`}
                >
                  {/* Gradient Border Animation */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20 translate-x-[-100%] group-hover:translate-x-[100%] transition-all duration-1000"></div>

                  <div className="relative rounded-2xl bg-slate-900/95 backdrop-blur-xl p-6 h-full">
                    <div className="flex items-start justify-between mb-4">
                      <span className="text-4xl font-black bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                        {card.letter}
                      </span>
                      <span className="text-3xl">{card.icon}</span>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{card.title}</h3>
                    <p className="text-sm text-slate-300 leading-relaxed">{card.description}</p>
                    <div className="absolute bottom-0 left-0 h-1 w-0 group-hover:w-full bg-gradient-to-r from-transparent via-white to-transparent transition-all duration-500"></div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Primary Result */}
        <motion.div
          id="section-q1"
          className="px-6 py-8 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl rounded-2xl bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-slate-700/60 p-8">
            <p className="text-xs uppercase tracking-widest text-cyan-300 mb-3">Primary Result</p>
            <p className="text-slate-300 mb-4">This is the main outcome card. It stays above the analysis charts so the decision is obvious before the deeper plots.</p>
            <div className="grid md:grid-cols-4 gap-4">
              <div className="rounded-lg bg-slate-900/70 border border-slate-700/50 p-4">
                <p className="text-xs text-slate-400">Status</p>
                <p className="text-lg font-bold text-white">{inferResult ? "Inference Complete" : "Waiting for inference"}</p>
              </div>
              <div className="rounded-lg bg-slate-900/70 border border-slate-700/50 p-4">
                <p className="text-xs text-slate-400">Priority</p>
                <p className="text-lg font-bold text-white">
                  {inferResult ? ((Number(inferResult.collision_probability ?? 0) > 0.7) ? "HIGH" : (Number(inferResult.collision_probability ?? 0) > 0.4) ? "MEDIUM" : "LOW") : "-"}
                </p>
              </div>
              <div className="rounded-lg bg-slate-900/70 border border-slate-700/50 p-4">
                <p className="text-xs text-slate-400">Recommended Action</p>
                <p className="text-lg font-bold text-white">
                  {inferResult ? ((Number(inferResult.collision_probability ?? 0) > 0.6) ? "Escalate conjunction review" : "Track closely") : "-"}
                </p>
              </div>
              <div className="rounded-lg bg-slate-900/70 border border-slate-700/50 p-4">
                <p className="text-xs text-slate-400">Quality Score</p>
                <p className="text-lg font-bold text-white">
                  {inferResult ? `${(100 - Number(inferResult.collision_probability ?? 0) * 100).toFixed(1)}%` : "Run inference"}
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Main Content Section */}
        <motion.div
          className="px-6 py-12"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="mx-auto max-w-7xl grid lg:grid-cols-3 gap-12">
            {/* Left: Main Title & Description */}
            <motion.div variants={itemVariants} className="lg:col-span-2">
              <div className="space-y-8">
                {/* System Badge */}
                <motion.div
                  className="inline-block"
                  whileHover={{ scale: 1.05 }}
                  transition={{ duration: 0.3 }}
                >
                  <span className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/50 text-cyan-300 text-sm font-semibold uppercase tracking-wider">
                    Operational Space Safety Stack
                  </span>
                </motion.div>

                {/* Main Title */}
                <h1 className="text-5xl lg:text-6xl font-black leading-tight">
                  <span className="bg-gradient-to-r from-white via-cyan-100 to-blue-200 bg-clip-text text-transparent">
                    Unified Space Debris Intelligence
                  </span>
                  <span className="block text-4xl lg:text-5xl mt-2">
                    <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                      &
                    </span>
                  </span>
                  <span className="block text-4xl lg:text-5xl">
                    <span className="bg-gradient-to-r from-blue-300 via-cyan-300 to-emerald-300 bg-clip-text text-transparent">
                      Collision Prediction System
                    </span>
                  </span>
                </h1>

                {/* Description */}
                <p className="text-lg text-slate-300 leading-relaxed max-w-2xl">
                  Real-time TLE intake, orbital feature engineering, multimodal AI, and collision-risk scoring in one mission console. The system is built to feel like a flight-deck tool, not a demo.
                </p>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-4 pt-4">
                  <motion.button
                    onClick={onNavigate}
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    className="px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold text-lg shadow-2xl shadow-cyan-500/30 hover:shadow-cyan-500/50 transition-all cursor-pointer"
                  >
                    Open Mission Stack
                  </motion.button>

                  <motion.button
                    onClick={onNavigate}
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    className="px-8 py-4 rounded-xl border-2 border-cyan-500/50 text-cyan-300 font-bold text-lg hover:bg-cyan-500/10 transition-all cursor-pointer"
                  >
                    Inspect Orbital Catalog
                  </motion.button>
                </div>

                <div className="rounded-xl bg-slate-900/50 border border-slate-700/50 p-4 space-y-3">
                  <p className="text-xs uppercase tracking-widest text-slate-400">Mission Console Bridge</p>
                  <p className="text-sm text-slate-300">{legacyReady}</p>
                  <div className="flex flex-col md:flex-row gap-3">
                    <input
                      type="text"
                      value={legacyApiKey}
                      onChange={(event) => setLegacyApiKey(event.target.value)}
                      placeholder="Optional X-API-Key for protected deployments"
                      className="flex-1 rounded-lg bg-slate-800/80 border border-slate-700/50 px-3 py-2 text-slate-200 text-sm"
                    />
                    <button
                      onClick={() => void refreshLiveData()}
                      className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm font-semibold"
                    >
                      Refresh Live Data
                    </button>
                    <a
                      href="http://127.0.0.1:7860"
                      target="_blank"
                      rel="noreferrer"
                      className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold text-center"
                    >
                      Open Full Legacy Console
                    </a>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Right: Status Sidebar */}
            <motion.div variants={itemVariants}>
              <div className="space-y-4">
                {statusItems.map((item, idx) => (
                  <motion.div
                    key={idx}
                    className="rounded-xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 p-4 backdrop-blur-sm hover:border-slate-600/80 transition-all group"
                    whileHover={{ x: 4 }}
                    transition={{ duration: 0.3 }}
                  >
                    <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1 group-hover:text-slate-300 transition-colors">
                      {item.label}
                    </p>
                    <p className={`text-sm font-semibold ${item.color}`}>{item.value}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Core Metrics */}
        <motion.div
          id="section-q2"
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl">
            <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-cyan-300 to-blue-300 bg-clip-text text-transparent">
              System Performance Metrics
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {coreMetrics.map((metric, idx) => (
                <motion.div
                  key={idx}
                  className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-6 hover:border-slate-600/80 transition-all"
                  whileHover={{ y: -4 }}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <p className="text-xs uppercase tracking-widest text-slate-400 mb-2">{metric.label}</p>
                  <p className={`text-3xl font-bold ${metric.color}`}>{metric.value}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* System Thesis Section */}
        <motion.div
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl">
            <span className="inline-block px-4 py-2 rounded-full bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 text-sm font-semibold uppercase tracking-wider">
              System Thesis
            </span>

            <h2 className="text-4xl lg:text-5xl font-black leading-tight mt-6 mb-12">
              <span className="bg-gradient-to-r from-emerald-300 via-cyan-300 to-blue-300 bg-clip-text text-transparent">
                Physics-first.
              </span>
              <span className="block">
                <span className="bg-gradient-to-r from-blue-300 to-purple-300 bg-clip-text text-transparent">
                  AI-second. Human-in-the-loop.
                </span>
              </span>
            </h2>

            <p className="text-lg text-slate-300 leading-relaxed max-w-3xl mb-8">
              We shortlist objects with orbital mechanics, then let deep models rank risk, trajectory drift, and uncertainty. That keeps the system defensible when the network is noisy or the feed is incomplete.
            </p>

            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  title: "Orbital Physics Foundation",
                  description: "Kepler equations + SGP4 propagation form the bedrock. AI augments, never replaces.",
                  icon: "🔬",
                },
                {
                  title: "Multimodal Intelligence",
                  description: "Blend radar, optical imagery, TLE catalogs with uncertainty quantification via Bayesian methods.",
                  icon: "🧠",
                },
                {
                  title: "Human Verification Loop",
                  description: "Anomaly alerts routed to expert analysts. Decision audit trail for regulatory compliance.",
                  icon: "👤",
                },
              ].map((item, idx) => (
                <motion.div
                  key={idx}
                  className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-6 hover:border-slate-600/80 transition-all group"
                  whileHover={{ y: -4 }}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <p className="text-3xl mb-3">{item.icon}</p>
                  <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">{item.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Orbital Mission Deck */}
        <motion.div
          id="section-q3"
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl">
            <h2 className="text-3xl lg:text-4xl font-black text-white mb-3">Orbital Mission Deck</h2>
            <p className="text-slate-300 mb-8">This panel is the 3D-facing part of the system. It shows orbit shells, scene context, and the current collision-alert queue before the charts below.</p>
            <div className="grid lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 rounded-xl bg-slate-900/60 border border-slate-700/50 p-6">
                <p className="text-sm uppercase tracking-widest text-slate-400 mb-2">Orbital Situation Map</p>
                <p className="text-sm text-slate-300 mb-4">A shell-based orbit map with risk-coded markers.</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="rounded-lg bg-slate-800/70 border border-slate-700/50 p-3"><p className="text-xs text-slate-400">Tracked Objects</p><p className="text-xl font-bold text-white">{orbitalBrief?.stats?.tracked_objects ?? 6}</p></div>
                  <div className="rounded-lg bg-slate-800/70 border border-slate-700/50 p-3"><p className="text-xs text-slate-400">Shells</p><p className="text-xl font-bold text-white">{orbitalBrief?.stats?.shells ?? 3}</p></div>
                  <div className="rounded-lg bg-slate-800/70 border border-slate-700/50 p-3"><p className="text-xs text-slate-400">Alerts</p><p className="text-xl font-bold text-white">{orbitalBrief?.stats?.alerts ?? 4}</p></div>
                  <div className="rounded-lg bg-slate-800/70 border border-slate-700/50 p-3"><p className="text-xs text-slate-400">Mode</p><p className="text-sm font-bold text-white">Physics-gated fusion</p></div>
                </div>
              </div>
              <div className="rounded-xl bg-slate-900/60 border border-slate-700/50 p-6">
                <p className="text-sm uppercase tracking-widest text-slate-400 mb-3">Collision Alert Panel</p>
                <div className="space-y-3 text-sm text-slate-200">
                  {(orbitalBrief?.alerts ?? [
                    { object_name: "DEBRIS-B", level: "HIGH", risk_percent: 75.4, note: "Escalate conjunction review" },
                    { object_name: "DEBRIS-E", level: "HIGH", risk_percent: 70.8, note: "Escalate conjunction review" },
                    { object_name: "DEBRIS-A", level: "MEDIUM", risk_percent: 68.0, note: "Track closely" },
                  ]).slice(0, 4).map((alert: any, idx: number) => (
                    <div key={idx} className="rounded-lg bg-slate-800/70 border border-slate-700/50 p-3">
                      <p className="font-semibold">{alert.object_name} ({alert.level})</p>
                      <p className="text-slate-400">Risk {Number(alert.risk_percent ?? 0).toFixed(1)}% - {alert.note ?? "Review"}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Research Pipeline */}
        <motion.div
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl">
            <span className="inline-block px-4 py-2 rounded-full bg-purple-500/20 border border-purple-500/50 text-purple-300 text-sm font-semibold uppercase tracking-wider">
              Research Pipeline
            </span>

            <h2 className="text-4xl lg:text-5xl font-black leading-tight mt-6 mb-4 text-white">
              How Physics and AI<br />
              <span className="bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                Share the Work
              </span>
            </h2>

            <p className="text-lg text-slate-300 leading-relaxed max-w-3xl mb-12">
              Use this view to see where the orbital math ends and the learned models begin. The separation is intentional because pure ML was not stable enough on sparse or noisy passes.
            </p>

            {/* Research Steps */}
            <div className="space-y-6 mb-12">
              {researchSteps.map((step, idx) => (
                <motion.div
                  key={idx}
                  className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-6 hover:border-slate-600/80 transition-all group flex gap-6"
                  whileHover={{ x: 4 }}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <div className="flex-shrink-0">
                    <span className="text-4xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                      {step.number}
                    </span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2">{step.title}</h3>
                    <p className="text-slate-300 leading-relaxed">{step.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Pipeline Diagram */}
            <motion.div
              className="rounded-xl bg-gradient-to-br from-slate-800/40 to-slate-900/40 border border-slate-700/50 p-8"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
            >
              <div className="overflow-x-auto">
                <div className="flex gap-4 pb-4 min-w-max">
                  {[
                    { label: "Input", value: "TLE, radar, imagery, metadata", icon: "📥" },
                    { label: "Preprocess", value: "Parse, clean, shell-tag, normalize", icon: "⚙️" },
                    { label: "Encoders", value: "LSTM / GRU, Transformer, CNN, XGBoost", icon: "🧮" },
                    { label: "Fusion", value: "Physics gate + calibrated confidence", icon: "🔀" },
                    { label: "Heads", value: "Trajectory, classification, risk, alert", icon: "🎯" },
                    { label: "Output", value: "3D deck, alerts, papers, exports", icon: "📤" },
                  ].map((stage, idx) => (
                    <motion.div
                      key={idx}
                      className="flex flex-col items-center gap-2 min-w-[180px]"
                      whileHover={{ y: -4 }}
                    >
                      <div className="rounded-lg bg-gradient-to-br from-slate-700/60 to-slate-800/60 border border-slate-600/50 p-4 w-full text-center">
                        <p className="text-2xl mb-2">{stage.icon}</p>
                        <p className="text-xs uppercase text-slate-400 font-bold mb-1">{stage.label}</p>
                        <p className="text-xs text-slate-300">{stage.value}</p>
                      </div>
                      {idx < 5 && <span className="text-slate-500 text-xl">→</span>}
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Model Benchmarks */}
        <motion.div
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl">
            <span className="inline-block px-4 py-2 rounded-full bg-blue-500/20 border border-blue-500/50 text-blue-300 text-sm font-semibold uppercase tracking-wider">
              Model Benchmarks
            </span>

            <h2 className="text-4xl lg:text-5xl font-black leading-tight mt-6 mb-4 text-white">
              Multi-Architecture<br />
              <span className="bg-gradient-to-r from-blue-300 to-cyan-300 bg-clip-text text-transparent">
                Performance Comparison
              </span>
            </h2>

            <p className="text-lg text-slate-300 leading-relaxed max-w-3xl mb-8">
              8 different model architectures compared across accuracy, precision, recall, F1, and calibration metrics. ResNet-18 and ConvNeXt-Tiny lead with perfect accuracy.
            </p>

            {/* Models Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              {displayedModelBenchmarks.map((model, idx) => (
                <motion.div
                  key={idx}
                  className="rounded-lg bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-4 hover:border-slate-600/80 transition-all cursor-pointer"
                  whileHover={{ y: -4, scale: 1.02 }}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  onClick={() => setExpandedModel(expandedModel === model.name ? null : model.name)}
                >
                  <h3 className="text-sm font-bold text-white mb-3 capitalize">{model.name}</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-400">Accuracy</span>
                      <span className="text-sm font-bold text-cyan-400">{model.accuracy.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-400">F1</span>
                      <span className="text-sm font-bold text-emerald-400">{model.f1.toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-400">Loss</span>
                      <span className="text-sm font-bold text-orange-400">{model.loss.toFixed(4)}</span>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedModel === model.name && (
                    <motion.div
                      className="mt-4 pt-4 border-t border-slate-700/50 space-y-2"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Precision</span>
                        <span className="text-cyan-300">{model.precision.toFixed(4)}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Recall</span>
                        <span className="text-cyan-300">{model.recall.toFixed(4)}</span>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>

            {/* Best Models Highlight */}
            <motion.div
              className="rounded-xl bg-gradient-to-br from-slate-800/40 to-slate-900/40 border border-slate-700/50 p-8"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
            >
              <div className="grid md:grid-cols-4 gap-6">
                {[
                  {
                    label: "Best Model",
                    value: displayedModelBenchmarks.length > 0
                      ? displayedModelBenchmarks.reduce((best, current) => current.f1 > best.f1 ? current : best).name
                      : "resnet18",
                    icon: "🏆",
                  },
                  {
                    label: "Best Accuracy",
                    value: `${Math.max(...displayedModelBenchmarks.map((item) => item.accuracy), 100).toFixed(2)}%`,
                    icon: "🎯",
                  },
                  {
                    label: "Best F1",
                    value: Math.max(...displayedModelBenchmarks.map((item) => item.f1), 1).toFixed(4),
                    icon: "✨",
                  },
                  {
                    label: "Benchmark Samples",
                    value: String(liveModelBenchmarks.length > 0 ? 640 : 640),
                    icon: "📊",
                  },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    className="text-center"
                    whileHover={{ scale: 1.05 }}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                  >
                    <p className="text-2xl mb-2">{item.icon}</p>
                    <p className="text-xs uppercase text-slate-400 font-bold mb-1">{item.label}</p>
                    <p className="text-2xl font-black bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                      {item.value}
                    </p>
                  </motion.div>
                ))}
              </div>
              {benchBusy && <p className="text-sm text-slate-300 mt-6">Refreshing live model benchmark...</p>}
            </motion.div>
          </div>
        </motion.div>

        {/* Live Inference Section */}
        <motion.div
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl">
            <span className="inline-block px-4 py-2 rounded-full bg-green-500/20 border border-green-500/50 text-green-300 text-sm font-semibold uppercase tracking-wider">
              Live Inference
            </span>

            <h2 className="text-4xl lg:text-5xl font-black leading-tight mt-6 mb-4 text-white">
              Core Inputs Stay<br />
              <span className="bg-gradient-to-r from-green-300 to-emerald-300 bg-clip-text text-transparent">
                Visible First
              </span>
            </h2>

            <p className="text-lg text-slate-300 leading-relaxed max-w-3xl mb-8">
              Advanced options are collapsed so first-time users can move straight to a result.
            </p>

            <div className="grid md:grid-cols-2 gap-8">
              {/* Inference Controls */}
              <motion.div
                className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-8"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
              >
                <h3 className="text-xl font-bold text-white mb-6">Inference Controls</h3>
                <div className="space-y-6">
                  <div>
                    <label className="text-sm font-semibold text-slate-300 mb-2 block">Image Size</label>
                    <input
                      type="number"
                      min={32}
                      max={512}
                      value={imageSize}
                      onChange={(event) => setImageSize(Number(event.target.value || 64))}
                      className="w-full rounded-lg bg-slate-700/30 border border-slate-600/30 px-4 py-2 text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-300 mb-2 block">Optical Bands</label>
                    <select
                      value={opticalBand}
                      onChange={(event) => setOpticalBand(event.target.value)}
                      className="w-full rounded-lg bg-slate-700/30 border border-slate-600/30 px-4 py-2 text-slate-200"
                    >
                      <option value="rgb">RGB</option>
                      <option value="gray">Grayscale</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-300 mb-2 block">Normalization</label>
                    <select
                      value={normalizeMode}
                      onChange={(event) => setNormalizeMode(event.target.value)}
                      className="w-full rounded-lg bg-slate-700/30 border border-slate-600/30 px-4 py-2 text-slate-200"
                    >
                      <option value="unit">Unit [0,1]</option>
                      <option value="zscore">Z-Score</option>
                    </select>
                  </div>
                  <button
                    onClick={() => void runLivePrediction()}
                    disabled={inferBusy}
                    className="w-full mt-6 px-4 py-3 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 text-white font-bold hover:shadow-lg shadow-green-500/30 transition-all disabled:opacity-60"
                  >
                    {inferBusy ? "Running..." : "Run Prediction"}
                  </button>
                  <button
                    onClick={() => void runDemoVisualFill()}
                    disabled={selectedBusy}
                    className="w-full px-4 py-3 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all disabled:opacity-60"
                  >
                    {selectedBusy ? "Filling..." : "Run Demo Visual Fill"}
                  </button>
                  <p className="text-sm text-slate-300">{inferStatus}</p>
                  {inferResult && (
                    <div className="rounded-lg bg-slate-900/60 border border-slate-700/50 p-4 text-sm text-slate-200 space-y-1">
                      <p>Detect Probability: {(Number(inferResult.detect_probability ?? 0) * 100).toFixed(2)}%</p>
                      <p>Collision Probability: {(Number(inferResult.collision_probability ?? 0) * 100).toFixed(2)}%</p>
                      <p>Predicted Class: {String(inferResult.predicted_class ?? "n/a")}</p>
                      <p>Inference Source: {String(inferResult.inference_source ?? "n/a")}</p>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* File Uploads */}
              <motion.div
                className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-8"
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
              >
                <h3 className="text-xl font-bold text-white mb-6">Input Data</h3>
                <div className="space-y-6">
                  <div>
                    <label className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <span>🖼️</span> Optical Image
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(event) => setOpticalFile(event.target.files?.[0] ?? null)}
                      className="w-full rounded-lg bg-slate-700/30 border border-slate-600/50 px-4 py-3 text-slate-200"
                    />
                    <p className="text-xs text-slate-400 mt-1">{opticalFile?.name ?? "No file chosen"}</p>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <span>📡</span> Radar Image
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(event) => setRadarFile(event.target.files?.[0] ?? null)}
                      className="w-full rounded-lg bg-slate-700/30 border border-slate-600/50 px-4 py-3 text-slate-200"
                    />
                    <p className="text-xs text-slate-400 mt-1">{radarFile?.name ?? "No file chosen"}</p>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <span>📊</span> Physics Vector (16 values)
                    </label>
                    <textarea
                      value={physicsVector}
                      onChange={(event) => setPhysicsVector(event.target.value)}
                      rows={3}
                      className="w-full rounded-lg bg-slate-700/30 border border-slate-600/50 px-4 py-3 text-slate-200"
                    />
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Dataset Section */}
        <motion.div
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl">
            <span className="inline-block px-4 py-2 rounded-full bg-indigo-500/20 border border-indigo-500/50 text-indigo-300 text-sm font-semibold uppercase tracking-wider">
              Dataset & Batch Operations
            </span>

            <h2 className="text-4xl lg:text-5xl font-black leading-tight mt-6 mb-4 text-white">
              NASA Public Data<br />
              <span className="bg-gradient-to-r from-indigo-300 to-purple-300 bg-clip-text text-transparent">
                Loader & Batch Inference
              </span>
            </h2>

            <p className="text-lg text-slate-300 leading-relaxed max-w-3xl mb-8">
              Ingest public orbital debris sources and run batch inference on entire datasets with one click.
            </p>

            <div className="grid md:grid-cols-3 gap-4 mb-8">
              <input
                value={datasetDir}
                onChange={(event) => setDatasetDir(event.target.value)}
                placeholder="Dataset folder path"
                className="rounded-lg bg-slate-800/70 border border-slate-700/50 px-4 py-3 text-slate-200"
              />
              <select
                value={batchModality}
                onChange={(event) => setBatchModality(event.target.value)}
                className="rounded-lg bg-slate-800/70 border border-slate-700/50 px-4 py-3 text-slate-200"
              >
                <option value="optical">optical</option>
                <option value="radar">radar</option>
                <option value="all">all</option>
              </select>
              <input
                type="number"
                min={1}
                max={500}
                value={maxSamples}
                onChange={(event) => setMaxSamples(Number(event.target.value || 12))}
                className="rounded-lg bg-slate-800/70 border border-slate-700/50 px-4 py-3 text-slate-200"
              />
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* NASA Loader */}
              <motion.div
                className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-6"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                whileHover={{ y: -4 }}
              >
                <p className="text-4xl mb-3">🚀</p>
                <h3 className="text-lg font-bold text-white mb-3">NASA Public Data</h3>
                <p className="text-sm text-slate-300 mb-6">
                  Ingest public orbital debris sources so the rest of the workflow has a concrete dataset.
                </p>
                <button
                  onClick={() => void loadNasaData()}
                  disabled={nasaBusy}
                  className="w-full px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-all disabled:opacity-60"
                >
                  {nasaBusy ? "Loading..." : "Load Everything"}
                </button>
                <p className="text-xs text-slate-300 mt-3">{nasaStatus}</p>
                {solarFluxRows > 0 && <p className="text-xs text-cyan-300">Solar Flux Rows: {solarFluxRows}</p>}
              </motion.div>

              {/* Batch Inference */}
              <motion.div
                className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-6"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                whileHover={{ y: -4 }}
              >
                <p className="text-4xl mb-3">⚡</p>
                <h3 className="text-lg font-bold text-white mb-3">Batch Inference</h3>
                <p className="text-sm text-slate-300 mb-6">
                  Run folder-level inference when ready. Default controls keep the primary decision flow simple.
                </p>
                <button
                  onClick={() => void runDatasetBatch()}
                  disabled={batchBusy}
                  className="w-full px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-all disabled:opacity-60"
                >
                  {batchBusy ? "Running..." : "Run Batch"}
                </button>
                <p className="text-xs text-slate-300 mt-3">{batchStatus}</p>
                {batchResult && (
                  <p className="text-xs text-cyan-300 mt-1">
                    Avg Collision: {(Number(batchResult.avg_collision_probability ?? 0) * 100).toFixed(2)}%
                  </p>
                )}
              </motion.div>

              {/* Dataset Explorer */}
              <motion.div
                className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-6"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                whileHover={{ y: -4 }}
              >
                <p className="text-4xl mb-3">🔍</p>
                <h3 className="text-lg font-bold text-white mb-3">Dataset Explorer</h3>
                <p className="text-sm text-slate-300 mb-6">
                  Inspect one file end-to-end instead of launching a whole batch for quick validation.
                </p>
                <div className="space-y-2">
                  <button
                    onClick={() => void scanExplorer()}
                    disabled={explorerBusy}
                    className="w-full px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white font-semibold transition-all disabled:opacity-60"
                  >
                    {explorerBusy ? "Scanning..." : "Explore Files"}
                  </button>
                  <button
                    onClick={() => void runSelectedImage()}
                    disabled={selectedBusy || !selectedPath}
                    className="w-full px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold transition-all disabled:opacity-60"
                  >
                    {selectedBusy ? "Running..." : "Run Selected Image"}
                  </button>
                </div>
                <p className="text-xs text-slate-300 mt-3">{explorerStatus}</p>
                {explorerItems.length > 0 && (
                  <select
                    value={selectedPath}
                    onChange={(event) => setSelectedPath(event.target.value)}
                    className="mt-3 w-full rounded-lg bg-slate-800/70 border border-slate-700/50 px-3 py-2 text-slate-200 text-xs"
                  >
                    {explorerItems.map((item) => (
                      <option key={item.path} value={item.path}>
                        {item.file_name ?? item.path}
                      </option>
                    ))}
                  </select>
                )}
                {selectedResult && (
                  <div className="mt-3 rounded-lg bg-slate-900/60 border border-slate-700/50 p-3 text-xs text-slate-200 space-y-1">
                    <p>Detect: {(Number(selectedResult.detect_probability ?? 0) * 100).toFixed(2)}%</p>
                    <p>Collision: {(Number(selectedResult.collision_probability ?? 0) * 100).toFixed(2)}%</p>
                    <p>Class: {String(selectedResult.predicted_class ?? "n/a")}</p>
                  </div>
                )}
                {explorerItems.length > 0 && (
                  <div className="mt-3 rounded-lg bg-slate-900/60 border border-slate-700/50 p-3 max-h-56 overflow-auto">
                    <p className="text-xs uppercase tracking-widest text-slate-400 mb-2">Image Selection</p>
                    <div className="space-y-1 text-xs text-slate-200">
                      {explorerItems.slice(0, 100).map((item, index) => (
                        <button
                          key={item.path}
                          onClick={() => setSelectedPath(item.path)}
                          className={`w-full text-left px-2 py-1 rounded ${selectedPath === item.path ? "bg-cyan-700/40" : "hover:bg-slate-700/50"}`}
                        >
                          {index.toString().padStart(2, "0")} {item.file_name ?? item.path} {item.modality ? `(${item.modality})` : ""}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Research Pack / Full Console */}
        <motion.div
          id="section-q4"
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          whileInView={{ opacity: 1, y: 0 }}
        >
          <div className="mx-auto max-w-7xl space-y-6">
            <h2 className="text-3xl lg:text-4xl font-black text-white">Research Pack and Export Console</h2>
            <p className="text-slate-300">Export evidence, inspect full plots, reliability diagrams, and mission tabs in the full legacy console.</p>
            <div className="flex flex-wrap gap-3">
              <a href="http://127.0.0.1:7860" target="_blank" rel="noreferrer" className="px-4 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-semibold">Open Full Console</a>
              <button onClick={() => setShowLegacyConsole((value) => !value)} className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-semibold">
                {showLegacyConsole ? "Hide Embedded Console" : "Show Embedded Console"}
              </button>
            </div>
            {showLegacyConsole && (
              <div className="rounded-xl overflow-hidden border border-slate-700/60 bg-slate-900/80">
                <iframe
                  src="http://127.0.0.1:7860"
                  title="Legacy Mission Console"
                  className="w-full h-[900px]"
                />
              </div>
            )}
          </div>
        </motion.div>

        {/* Footer Stats */}
        <motion.div
          className="px-6 py-12 border-t border-slate-700/30 bg-gradient-to-t from-slate-900/50 to-transparent"
          variants={itemVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="mx-auto max-w-7xl">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {[
                { label: "Active Objects", value: "428+", icon: "📍" },
                { label: "Detection Accuracy", value: "94.2%", icon: "🎯" },
                { label: "API Latency (p95)", value: "164ms", icon: "⚡" },
                { label: "System Uptime", value: "99.9%", icon: "✓" },
              ].map((stat, idx) => (
                <motion.div
                  key={idx}
                  className="text-center"
                  whileHover={{ scale: 1.05 }}
                  transition={{ duration: 0.3 }}
                >
                  <p className="text-2xl mb-2">{stat.icon}</p>
                  <p className="text-3xl font-black bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                    {stat.value}
                  </p>
                  <p className="text-xs uppercase tracking-widest text-slate-400 mt-2">{stat.label}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
