# PyPI SEO Action List - All 8 Repositories

## ✅ COMPLETED

### PyCostAudit
- ✅ Enhanced description with SEO keywords
- ✅ Keywords expanded: 5 → 20
- ✅ Classifiers added: 23 total
- ✅ Project URLs added: Documentation, Changelog, Source, Discussions
- 📍 Status: **LIVE ON PyPI v0.9.0**
- 📊 Need: Blog post, GitHub topics, Reddit announcement

---

## ⏳ TODO - Next 7 Repositories

### Template to Apply to Each Repository:

```bash
# 1. Clone repository
git clone https://github.com/Mullassery/[REPO_NAME]
cd [REPO_NAME]

# 2. Update pyproject.toml with:
#    - New description (SEO-optimized)
#    - Keywords list (20-25 items)
#    - Classifiers (20+ items)
#    - Project URLs (6-7 links)

# 3. Commit and push
git add pyproject.toml
git commit -m "docs: Improve PyPI metadata for SEO discoverability"
git push

# 4. Build and publish (after each repo update)
python -m build
python -m twine upload dist/* --repository pypi
```

---

## 📦 Repository Priority & Actions

### 🥇 Priority 1: ClusterAudienceKit
**Current:** v0.1.0 on PyPI | 0 stars | No keywords
**Action:** 
1. Update `pyproject.toml` with 25 keywords
2. Add 20+ classifiers (see guide)
3. Expand description to 160 chars
4. Add project URLs
5. Build & upload to PyPI

**Keywords to Add:**
`clustering, customer-segmentation, rfm-analysis, martech, audience-segmentation, customer-analytics, machine-learning, k-means, segmentation-engine, crm, customer-lifetime-value, cohort-analysis, audience-targeting, marketing-automation, email-marketing, retargeting, customer-scoring, behavioral-analytics, data-science, python-library, real-time-processing, streaming-data, marketing-tech, audience-modeling`

---

### 🥈 Priority 2: prismnote (PrismNote)
**Current:** v0.4.5 on PyPI | 0 stars | Minimal keywords
**Action:**
1. Update description (160 char SEO version)
2. Add 24 keywords
3. Add 20+ classifiers
4. Add project URLs
5. Ensure README is compelling with examples
6. Build & upload

**Keywords to Add:**
`jupyter, notebook, data-science, sql-notebook, data-analytics, python-notebook, spark, bigquery, snowflake, redshift, postgres, mysql, cloud-warehouse, ide, code-editor, rust-performance, react-ui, web-app, collaboration, data-exploration, exploratory-analysis, analytics-platform, query-builder, ai-assistant, ml-development`

---

### 🥉 Priority 3: PyRoboFrames
**Current:** v1.1.0 on PyPI | 0 stars | Basic keywords
**Action:**
1. Update description with SEO focus
2. Add 22 keywords
3. Add classifiers (robotics, ML)
4. Add project URLs
5. Build & upload

**Keywords to Add:**
`robotics, robot-learning, ml-dataloader, leerobot, dataset-loader, computer-vision, video-processing, mlx, pytorch, jax, numpy, data-pipeline, machine-learning, reinforcement-learning, edge-ai, apple-silicon, video-decode, zero-copy, deep-learning, neural-networks, training-framework, data-preprocessing`

---

### Priority 4: PyRoboVision
**Current:** v0.5.0 on PyPI | 0 stars | Minimal metadata
**Action:**
1. Update description
2. Add 23 keywords (autonomous driving, perception, etc.)
3. Add classifiers
4. Add project URLs
5. Build & upload

**Keywords:**
`autonomous-driving, computer-vision, perception, lidar-fusion, 3d-object-detection, bev-bird-eye-view, panoptic-segmentation, semantic-segmentation, camera-calibration, vision-language-models, clip, segment-anything, foundation-models, self-driving, robotics, deep-learning, neural-networks, pytorch, image-processing, sensor-fusion, automotive, safety-critical, ml-ops, edge-ai`

---

### Priority 5: Pyvectorhound
**Current:** v0.1.0 on PyPI | 0 stars | No keywords
**Action:**
1. Update description (RAG debugging focus)
2. Add 21 keywords
3. Add classifiers (NLP, RAG, debugging)
4. Add project URLs
5. Build & upload

**Keywords:**
`rag, retrieval-augmented-generation, vector-search, embedding, semantic-search, llm, large-language-models, information-retrieval, search-ranking, evaluation-metrics, bm25, reranking, debugging, diagnostics, nlp, natural-language-processing, similarity-search, faiss, elasticsearch, pinecone, milvus, ai-debugging`

---

### Priority 6: Statguardian
**Current:** v0.1.0 on PyPI | 0 stars | No keywords
**Action:**
1. Update description (data quality, 13x faster)
2. Add 23 keywords
3. Add classifiers (data quality, testing, etc.)
4. Add project URLs
5. Build & upload

**Keywords:**
`data-quality, data-validation, schema-validation, data-testing, data-contracts, pandas, polars, duckdb, data-pipeline, etl, data-engineering, data-governance, drift-detection, anomaly-detection, outlier-detection, automated-testing, data-integrity, data-profiling, statistical-analysis, python-library, machine-learning, mlops, data-ops, data-observability`

---

### Priority 7: StreamXL
**Current:** v0.4.0 on PyPI | 0 stars | No keywords
**Action:**
1. Update description (46x faster, memory-efficient)
2. Add 20 keywords
3. Add classifiers (spreadsheets, file formats)
4. Add project URLs
5. Build & upload

**Keywords:**
`excel, xlsx, spreadsheet, streaming, file-parsing, data-loading, performance, rust, python-api, memory-efficient, big-data, etl, data-pipeline, file-handling, openpyxl-alternative, pandas-io, data-engineering, batch-processing, file-processing, performance-optimization`

---

## 🚀 Quick Setup Script

Create this as `update_pypi_metadata.sh`:

```bash
#!/bin/bash

REPOS=(
    "ClusterAudienceKit"
    "prismnote"
    "PyRoboFrames"
    "PyRoboVision"
    "Pyvectorhound"
    "Statguardian"
    "StreamXL"
)

for repo in "${REPOS[@]}"; do
    echo "📦 Updating $repo..."
    cd ~/$repo
    
    # Update pyproject.toml (requires manual edit with template)
    echo "  ⚠️  Please manually update pyproject.toml with SEO metadata"
    echo "     See PyPI_SEO_OPTIMIZATION.md for template"
    
    # Verify it's valid
    python -m build --wheel 2>/dev/null && echo "  ✅ Build successful"
    
    # Show current version
    version=$(python -c "from pyproject_toml import load_toml; print(load_toml('pyproject.toml')['project']['version'])" 2>/dev/null || echo "Unknown")
    echo "  Version: $version"
    echo ""
done
```

---

## 📋 Verification Checklist

After updating each repo, verify:

- [ ] Description is 60-160 characters with keywords
- [ ] Keywords list has 20-25 items
- [ ] Classifiers include: Development Status, Topic, Python versions
- [ ] Project URLs all work (test by clicking)
- [ ] README renders properly on PyPI
- [ ] Build succeeds: `python -m build`
- [ ] Upload succeeds: `python -m twine upload dist/*`
- [ ] PyPI page displays correctly: `https://pypi.org/project/[package]/`

---

## 📊 Expected Timeline

**Week 1:** Update PyProject.toml files (all 7 repos)
**Week 2:** Build & publish to PyPI (all 7 repos)
**Month 2:** Create blog posts + GitHub announcements
**Month 3:** Submit to Awesome Python, Python Weekly
**Month 6:** Monitor PyPI search rankings, adjust keywords

---

## 🎯 Success Metrics

Track these over 6 months:

| Metric | Baseline | Target (6mo) |
|--------|----------|--------------|
| Google search results | 0 | 50+ |
| PyPI search results | None | Top 10 |
| GitHub stars | 0 | 5-20 |
| Monthly downloads | 0 | 50+ |
| External links | 0 | 10+ |
| Blog mentions | 0 | 3+ |

---

## 💡 Pro Tips

1. **Use specific keywords** - "llm-cost-tracking" beats "cost tracking"
2. **Include problem + solution** - "Debug retrieval failures in RAG systems"
3. **Add numbers** - "13x faster than pandera" gets attention
4. **Match PyPI classifiers** - Use exact names from PyPI classifier list
5. **Add badges** - PyPI, License, Python versions, Build status
6. **Write examples** - README should have 3-5 runnable examples

---

## 📝 Notes

- All updates are non-breaking changes
- Can be done incrementally (one repo at a time)
- No need to bump version numbers
- PyPI updates take 5-15 minutes to propagate
- Test locally first: `python -m build`

