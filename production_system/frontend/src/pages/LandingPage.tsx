import { motion } from "framer-motion";
import { type ReactElement } from "react";

interface LandingPageProps {
  onNavigate?: () => void;
}

export function LandingPage({ onNavigate }: LandingPageProps): ReactElement {
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
      letter: "Q1",
      title: "TLE Intake",
      description: "Ingest CelesTrak, Space-Track, and local catalogs",
      icon: "📡",
      color: "from-blue-600 to-cyan-600",
      borderColor: "border-blue-500",
    },
    {
      letter: "Q2",
      title: "Fusion Engine",
      description: "Blend orbital physics with multimodal AI",
      icon: "⚡",
      color: "from-purple-600 to-pink-600",
      borderColor: "border-purple-500",
    },
    {
      letter: "Q3",
      title: "Orbital Deck",
      description: "Inspect 3D tracks, alerts, and uncertainty",
      icon: "🌐",
      color: "from-emerald-600 to-teal-600",
      borderColor: "border-emerald-500",
    },
    {
      letter: "Q4",
      title: "Research Pack",
      description: "Export evidence for paper and deployment",
      icon: "📦",
      color: "from-orange-600 to-red-600",
      borderColor: "border-orange-500",
    },
  ];

  const statusItems = [
    { label: "TLE STREAMS", value: "CelesTrak / Space-Track", color: "text-cyan-400" },
    { label: "RISK ENGINE", value: "Physics + AI Fusion", color: "text-purple-400" },
    { label: "VISUALIZATION", value: "3D Shell Deck", color: "text-emerald-400" },
    { label: "STATUS", value: "Ready", color: "text-green-400" },
    { label: "SECURITY", value: "Open + RL(180/min)", color: "text-yellow-400" },
    { label: "ACCESS", value: "ANONYMOUS", color: "text-slate-400" },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
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

        {/* System Thesis Section */}
        <motion.div
          className="px-6 py-12 border-t border-slate-700/30"
          variants={itemVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="mx-auto max-w-7xl">
            <motion.div className="space-y-6" whileInView={{ opacity: 1, y: 0 }}>
              <span className="inline-block px-4 py-2 rounded-full bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 text-sm font-semibold uppercase tracking-wider">
                System Thesis
              </span>

              <h2 className="text-4xl lg:text-5xl font-black leading-tight">
                <span className="bg-gradient-to-r from-emerald-300 via-cyan-300 to-blue-300 bg-clip-text text-transparent">
                  Physics-first.
                </span>
                <span className="block">
                  <span className="bg-gradient-to-r from-blue-300 to-purple-300 bg-clip-text text-transparent">
                    AI-second. Human-in-the-loop.
                  </span>
                </span>
              </h2>

              <div className="grid md:grid-cols-3 gap-8 mt-12">
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
            </motion.div>
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
