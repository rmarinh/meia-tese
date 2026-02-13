# Master's Thesis Implementation Plan
## Automated Software Testing using Multi-Agent Systems (MAS) and Large Language Models (LLMs)

**Author**: Rui Marinho (1171602)
**Supervisor**: Constantino Martins
**Program**: MEIA - Master in Artificial Intelligence Engineering, ISEP

---

## Phase 1: Research Questions Definition

### 1.1 Security & Privacy Research Questions (From PSGEIA Paper - Already Defined)

**RQ1 (Security/Privacy Risks)**: What predominant security and privacy risks are associated with LLM-based Multi-Agent Systems in enterprise software testing environments?

**RQ2 (Mitigation Strategies)**: What architectural patterns and mitigation strategies (e.g., sandboxing, PII scrubbing) are proposed in the literature to secure Agent-Computer Interfaces (ACI) and prevent data leakage?

### 1.2 Core Project Research Questions (NEW - To Be Defined)

**RQ3 (Effectiveness)**: How effective are Multi-Agent Systems powered by Large Language Models in automated software testing compared to traditional testing approaches?
- Sub-questions:
  - RQ3.1: What metrics are used to evaluate MAS-based testing effectiveness (coverage, bug detection rate, false positives)?
  - RQ3.2: What are the performance benchmarks for different MAS architectures in testing contexts?

**RQ4 (Architecture & Design)**: What architectural patterns and design principles are most effective for implementing MAS-based automated testing systems?
- Sub-questions:
  - RQ4.1: How do different agent collaboration models (hierarchical, peer-to-peer, hybrid) impact testing outcomes?
  - RQ4.2: What role specialization patterns exist for testing agents (coder, tester, reviewer, debugger)?

**RQ5 (Practical Implementation)**: What are the practical challenges and solutions for deploying MAS-based testing in real-world software development workflows?
- Sub-questions:
  - RQ5.1: How do MAS-based testing systems integrate with existing CI/CD pipelines?
  - RQ5.2: What is the cost-benefit analysis (token cost vs. developer time) for different testing scenarios?

**RQ6 (LLM Selection & Configuration)**: How do different Large Language Model choices and configurations impact the performance of Multi-Agent testing systems?
- Sub-questions:
  - RQ6.1: What are the trade-offs between proprietary models (GPT-4) vs. open-weights models (Llama, CodeLlama)?
  - RQ6.2: How do fine-tuning strategies compare to prompt engineering for testing agents?

---

## Phase 2: Extended Literature Review (Following PRISMA)

### 2.1 Security & Privacy Literature (COMPLETED - From PSGEIA Paper)
- **Status**: 15 studies selected and analyzed
- **Databases**: IEEE Xplore, ACM Digital Library
- **Period**: 2016-2026
- **Key Findings**: Data Leakage, Adversarial Manipulation, Unsafe Code Generation risks
- **Action**: Integrate into thesis Chapter 2 (Literature Review - Security & Privacy section)

### 2.2 MAS Architecture & Testing Effectiveness Literature (TO DO)

**Search Strategy**:
```
Context: "Software Testing" OR "Test Generation" OR "Automated Testing" OR "Unit Testing"
Intervention: "Multi-Agent" OR "MAS" OR "LLM" OR "Large Language Model" OR "GPT" OR "Code Generation"
Focus: "Architecture" OR "Effectiveness" OR "Performance" OR "Benchmark" OR "Evaluation"
```

**Target Studies**: 20-30 papers
**Databases**: IEEE Xplore, ACM Digital Library, arXiv (for recent preprints)
**Period**: 2020-2026

**Inclusion Criteria**:
- IC1: Studies presenting MAS architectures for software testing/development
- IC2: Studies with empirical evaluation of LLM-based testing tools
- IC3: Studies reporting quantitative metrics (coverage, bug detection, pass@k)
- IC4: Framework papers (MetaGPT, ChatDev, SWE-agent, AutoGPT, etc.)

**Exclusion Criteria**:
- EC1: Single-agent LLM approaches without multi-agent coordination
- EC2: Studies lacking empirical validation
- EC3: Non-English publications
- EC4: Opinion pieces without technical evaluation

**Key Papers to Include**:
1. MetaGPT (Hong et al., 2024)
2. ChatDev (Qian et al., 2024)
3. SWE-agent (Yang et al., 2024)
4. Mutation-Guided LLM Testing at Meta (Harman et al., 2025)
5. Fine-tuned LLMs for Mobile Testing (Hoffmann et al., 2024)
6. Large-scale Fine-tuning Study (Shang et al., 2025)

### 2.3 Practical Implementation & CI/CD Integration Literature (TO DO)

**Search Strategy**:
```
Context: "Software Testing" OR "CI/CD" OR "Continuous Integration"
Intervention: "LLM" OR "Large Language Model" OR "Agent" OR "Autonomous"
Focus: "Pipeline" OR "Integration" OR "Deployment" OR "Production" OR "Industrial"
```

**Target Studies**: 10-15 papers/industry reports
**Sources**: IEEE, ACM, Industry white papers (Microsoft, Meta, Google)

---

## Phase 3: Thesis Chapter Structure

### Chapter 1: Introduction (NEW CONTENT)
**Length**: 8-12 pages

**Content**:
1. **Context & Motivation** (2-3 pages)
   - Evolution of software testing (manual → automated → AI-powered)
   - Emergence of LLMs in software engineering
   - Rise of Multi-Agent Systems for complex tasks
   - Industry demand for autonomous testing solutions

2. **Problem Statement** (2 pages)
   - Limitations of traditional automated testing (brittle scripts, poor coverage)
   - Challenges of single-agent LLM approaches (context limits, lack of specialization)
   - Security and privacy concerns in agentic testing
   - Gap between research prototypes and production deployment

3. **Research Questions** (1-2 pages)
   - Present all 6 RQs (RQ1-RQ6) with justification
   - Explain how they relate to each other
   - Map RQs to thesis chapters

4. **Objectives** (1 page)
   - Primary: Design and validate a secure MAS architecture for automated testing
   - Secondary: Comprehensive SLR on MAS testing
   - Secondary: Prototype implementation with privacy-by-design
   - Secondary: Empirical evaluation on real-world benchmarks

5. **Contributions** (1 page)
   - Systematic literature review covering security, architecture, and effectiveness
   - Taxonomy of MAS testing architectures
   - Secure-by-design reference architecture
   - Prototype implementation and evaluation
   - Best practices for industrial deployment

6. **Thesis Structure** (1 page)
   - Brief overview of each chapter

**Sources**: Introduction from PSGEIA paper (adapt and expand)

---

### Chapter 2: Literature Review (HYBRID - Combine PSGEIA + New Research)
**Length**: 30-40 pages

#### 2.1 Methodology (PRISMA Protocol)
**Length**: 4-5 pages
- Research questions (all 6 RQs)
- Search strategy (multiple search strings for different RQ domains)
- Inclusion/Exclusion criteria
- Quality assessment criteria
- Data extraction process
- PRISMA flow diagram (combined for all searches)

**Source**: Methodology section from PSGEIA paper + extensions for RQ3-RQ6

#### 2.2 Study Selection and Characteristics
**Length**: 3-4 pages
- Total studies selected (~40-50 papers)
- Bibliometric analysis (temporal distribution, venues, models used)
- Overview table of selected studies

**Source**: Results section from PSGEIA paper + new studies

#### 2.3 Multi-Agent Systems for Software Testing (NEW)
**Length**: 8-10 pages
- Evolution of MAS in software engineering
- Agent architectures (hierarchical, peer-to-peer, hybrid)
- Role specialization patterns (coder, tester, reviewer, debugger, architect)
- Communication protocols and coordination mechanisms
- Major frameworks comparison (MetaGPT, ChatDev, SWE-agent, AutoGPT)
- Agent-Computer Interface (ACI) design patterns

**Addresses**: RQ4

#### 2.4 LLM Selection and Configuration (NEW)
**Length**: 6-8 pages
- Proprietary vs. open-weights models trade-offs
- Model capabilities for code understanding (GPT-4, Claude, Llama, CodeLlama)
- Fine-tuning vs. prompt engineering strategies
- Context window limitations and solutions
- Cost analysis (token costs, inference latency)
- Reasoning gap in smaller models

**Addresses**: RQ6

#### 2.5 Effectiveness and Performance Evaluation (NEW)
**Length**: 6-8 pages
- Evaluation metrics taxonomy (coverage, pass@k, bug detection, mutation score)
- Benchmark datasets (HumanEval, MBPP, SWE-bench, Defects4J)
- Comparative studies (MAS vs. traditional testing)
- Performance results from literature
- Limitations of current benchmarks

**Addresses**: RQ3

#### 2.6 Security and Privacy Challenges (FROM PSGEIA PAPER)
**Length**: 6-8 pages
- Grounding gap and hallucination risks
- Data leakage taxonomy (IP exfiltration, PII exposure)
- Adversarial manipulation (prompt injection, trojan comments)
- Unsafe code generation (slopsquatting, typosquatting)
- Deep dive: Attack vector analysis
  - Slopsquatting attack chain
  - Indirect prompt injection via code comments
  - Semantic data exfiltration

**Addresses**: RQ1

**Source**: Section III.D and III.E from PSGEIA paper

#### 2.7 Mitigation Strategies and Secure Architectures (FROM PSGEIA PAPER)
**Length**: 6-8 pages
- Three-layer mitigation taxonomy
  - Model-centric (local LLMs, fine-tuning)
  - Pipeline-centric (ACI hardening, sandboxing)
  - Algorithmic (mutation testing, chaos engineering)
- Deep dive: Emerging architectures
  - Orchestrated isolation (DURA-CPS)
  - Systematic robustness (combinatorial testing)
  - Static analysis augmentation
- Human-in-the-loop collaboration models

**Addresses**: RQ2

**Source**: Section III.F and III.G from PSGEIA paper

#### 2.8 Industrial Deployment and CI/CD Integration (NEW)
**Length**: 4-5 pages
- Integration patterns for existing pipelines
- Shadow mode deployment
- Cost-benefit analysis
- Organizational adoption challenges
- Case studies from industry (Meta, Microsoft, GitHub Copilot)

**Addresses**: RQ5

#### 2.9 Regulatory and Compliance Considerations (FROM PSGEIA PAPER)
**Length**: 4-5 pages
- EU AI Act implications (high-risk systems classification)
- GDPR compliance (data minimization, purpose limitation)
- Liability and shared responsibility model
- Transparency obligations (chain-of-thought logging)
- Data Protection Impact Assessment (DPIA) framework for agentic testing

**Source**: Section IV.G and IV.H from PSGEIA paper

#### 2.10 Discussion and Research Gaps
**Length**: 3-4 pages
- Synthesis of findings across all RQs
- Identified gaps in current research
- Challenges in evaluation and reproducibility
- Ethical and environmental considerations
- Justification for proposed work

**Source**: Discussion section from PSGEIA paper + synthesis of new literature

---

### Chapter 3: Proposed Architecture (NEW CONTENT)
**Length**: 15-20 pages

#### 3.1 Requirements Analysis
**Length**: 3-4 pages
- Functional requirements (test generation, execution, validation)
- Non-functional requirements (security, privacy, performance, scalability)
- Regulatory requirements (GDPR, AI Act compliance)
- Constraints and assumptions

#### 3.2 High-Level Architecture
**Length**: 4-5 pages
- System overview diagram
- Component identification
- Communication flows
- Technology stack justification

#### 3.3 Agent Architecture and Role Design
**Length**: 4-5 pages
- Agent roles and responsibilities
  - Planning Agent (decomposes testing tasks)
  - Code Agent (generates test code)
  - Execution Agent (runs tests in sandboxed environment)
  - Validation Agent (reviews test quality)
  - Security Agent (scans for vulnerabilities)
- Agent collaboration protocol
- Task allocation and scheduling
- Conflict resolution mechanisms

#### 3.4 Security-by-Design Implementation
**Length**: 4-5 pages
- Sandbox architecture (containerization, network isolation)
- Data flow security (PII scrubbing, context minimization)
- ACI hardening (permission model, tool access control)
- Audit logging and chain-of-thought tracking
- Fail-safe mechanisms

#### 3.5 LLM Integration Strategy
**Length**: 2-3 pages
- Model selection rationale
- Local vs. API-based execution trade-offs
- Prompt engineering templates
- Context management (RAG, semantic chunking)
- Fallback strategies for model failures

**Addresses**: RQ2, RQ4, RQ6 (architectural response)

---

### Chapter 4: Implementation (NEW CONTENT)
**Length**: 12-18 pages

#### 4.1 Technology Stack
**Length**: 2-3 pages
- Programming language (Python)
- LLM integration (OpenAI API, local Llama/Ollama)
- Agent framework (LangChain, AutoGen, CrewAI, or custom)
- Containerization (Docker)
- Testing frameworks (pytest, unittest)
- CI/CD integration (GitHub Actions)

#### 4.2 Core Components Implementation
**Length**: 6-8 pages
- Agent implementation details (code snippets, class diagrams)
- Communication protocol implementation
- Sandbox environment setup
- Security controls implementation
- Prompt templates and engineering patterns
- Context management and RAG implementation

#### 4.3 Workflow Implementation
**Length**: 3-4 pages
- Test generation workflow (from requirements to test code)
- Test execution workflow (sandboxed execution, result collection)
- Validation and review workflow
- Security scanning workflow
- Human-in-the-loop approval gates

#### 4.4 Integration with Development Environment
**Length**: 2-3 pages
- Git repository integration
- IDE plugin/CLI interface
- CI/CD pipeline integration
- Monitoring and logging setup

**Addresses**: RQ4, RQ5 (practical implementation)

---

### Chapter 5: Experimental Validation (NEW CONTENT)
**Length**: 15-20 pages

#### 5.1 Experimental Design
**Length**: 3-4 pages
- Research hypotheses (derived from RQs)
- Evaluation metrics
  - Coverage metrics (line, branch, mutation)
  - Effectiveness metrics (bug detection rate, false positives)
  - Efficiency metrics (time, token cost)
  - Security metrics (vulnerability detection, leakage prevention)
- Benchmark datasets selection
- Baseline comparisons (traditional tools, single-agent LLM)
- Experimental setup and environment

#### 5.2 Effectiveness Evaluation (RQ3)
**Length**: 4-5 pages
- Test coverage results
- Bug detection results
- Comparison with baselines (EvoSuite, Randoop, GitHub Copilot)
- Statistical significance analysis
- Qualitative analysis of generated tests

#### 5.3 Security Evaluation (RQ1 & RQ2)
**Length**: 3-4 pages
- Security testing methodology
- Attempted attacks (prompt injection, data exfiltration, slopsquatting)
- Mitigation effectiveness results
- Privacy compliance verification (GDPR checks)
- Audit log analysis

#### 5.4 Performance and Cost Analysis (RQ6)
**Length**: 2-3 pages
- Execution time measurements
- Token consumption and cost analysis
- Scalability testing results
- Resource utilization (CPU, memory, network)

#### 5.5 Ablation Studies
**Length**: 2-3 pages
- Impact of different agent architectures (remove roles, change collaboration)
- Impact of LLM model choice (GPT-4 vs. GPT-3.5 vs. Llama)
- Impact of security controls (sandbox overhead)

#### 5.6 Discussion of Results
**Length**: 2-3 pages
- Interpretation of findings
- Threats to validity (internal, external, construct)
- Limitations of the study
- Lessons learned

**Addresses**: RQ3, RQ6 (empirical validation)

---

### Chapter 6: Conclusions and Future Work (NEW CONTENT)
**Length**: 6-8 pages

#### 6.1 Summary of Contributions
**Length**: 2 pages
- Recap of main contributions
- How each RQ was addressed

#### 6.2 Answers to Research Questions
**Length**: 2-3 pages
- Explicit answers to each RQ (RQ1-RQ6)
- Synthesis of theoretical and empirical findings

#### 6.3 Practical Implications
**Length**: 1-2 pages
- Recommendations for practitioners
- Guidelines for secure MAS deployment
- Best practices for industrial adoption

#### 6.4 Limitations
**Length**: 1 page
- Study limitations
- Generalizability constraints
- Benchmark limitations

#### 6.5 Future Research Directions
**Length**: 1-2 pages
- Self-healing pipelines
- Explainability and chain-of-thought logging
- Multi-modal agents (code + UI testing)
- Specialized benchmarks for security evaluation
- Long-term empirical studies in industry

**Source**: Conclusions and Future Work from PSGEIA paper (adapt and expand)

---

## Phase 4: Bibliography Integration

### 4.1 From PSGEIA Paper (15 references - COMPLETED)
- Sternak et al., 2025 (Prompt leakage)
- Owotogbe, 2025 (Chaos engineering)
- Nayyeri et al., 2025 (Privacy-preserving recommender)
- Bradbury et al., 2025 (Data leakage in HumanEval)
- Traykov, 2024 (Security testing framework)
- Chandrasekaran et al., 2025 (Combinatorial testing)
- Zhao et al., 2024 (Malicious code in model hubs)
- Wang et al., 2024 (Agent alignment)
- Srinivasan et al., 2025 (DURA-CPS)
- Loevenich et al., 2025 (Attack automation)
- Sallou et al., 2024 (Threats in SE LLMs)
- Harman et al., 2025 (Meta mutation testing)
- Hoffmann et al., 2024 (Mobile testing)
- Yang et al., 2024 (LLM unit test evaluation)
- Shang et al., 2025 (Fine-tuning study)

**Plus 5 foundational references**:
- Wang et al., 2023 (Software Testing with LLM: Survey)
- Hong et al., 2024 (MetaGPT)
- Qian et al., 2024 (ChatDev)
- Yang et al., 2024 (SWE-agent)
- Page et al., 2021 (PRISMA 2020 guidelines)

**Action**: Add all to `mainbibliography.bib`

### 4.2 Additional References Needed (~25-30 papers)

**MAS Architecture & Frameworks**:
1. AutoGPT framework
2. BabyAGI
3. CrewAI
4. LangChain agents
5. Multi-agent coordination surveys
6. Agent communication protocols
7. Role-based agent systems

**LLM Code Understanding**:
8. CodeBERT
9. CodeT5
10. StarCoder
11. Code Llama
12. Codex/GPT-4 for code
13. Comparative LLM studies

**Testing Benchmarks**:
14. HumanEval (Chen et al.)
15. MBPP
16. SWE-bench
17. Defects4J
18. Code contests datasets

**Traditional Testing Tools (Baselines)**:
19. EvoSuite
20. Randoop
21. Search-based testing surveys
22. Mutation testing foundations

**Security & Privacy Foundations**:
23. GDPR technical guidance
24. EU AI Act text
25. Privacy-by-design principles
26. Secure software development
27. Container security

**Industrial Case Studies**:
28. GitHub Copilot evaluations
29. Amazon CodeWhisperer
30. Google's AI coding assistants

**Action**: Conduct extended literature search for RQ3-RQ6

### 4.3 Bibliography Format
- Use `authoryear-comp` style (already configured in main.tex)
- Ensure all references have DOI/URL where applicable
- Verify BibTeX formatting for IEEE/ACM sources

---

## Phase 5: Content Assembly Workflow

### 5.1 Chapter 1: Introduction (Week 1)
1. Draft context and motivation section
2. Refine problem statement
3. Finalize all 6 RQs
4. Write objectives and contributions
5. Review with supervisor

### 5.2 Chapter 2: Literature Review (Weeks 2-4)
1. **Week 2**: Conduct extended literature search for RQ3-RQ6
   - Download and screen papers
   - Apply inclusion/exclusion criteria
   - Extract data to structured form
2. **Week 3**: Write new sections (2.3-2.5, 2.8)
   - MAS architectures section
   - LLM selection section
   - Effectiveness evaluation section
   - CI/CD integration section
3. **Week 4**: Integrate PSGEIA content (2.6-2.7, 2.9)
   - Copy security challenges section from PSGEIA
   - Copy mitigation strategies section from PSGEIA
   - Copy regulatory section from PSGEIA
   - Write synthesis and discussion
4. Review methodology section to ensure all RQs covered

### 5.3 Chapter 3: Architecture (Week 5)
1. Design high-level architecture diagram
2. Define agent roles and responsibilities
3. Document security-by-design decisions
4. Create detailed component diagrams
5. Review with supervisor

### 5.4 Chapter 4: Implementation (Weeks 6-8)
1. **Week 6**: Set up development environment and technology stack
2. **Week 7**: Implement core agent components
3. **Week 8**: Implement security controls and integration
4. Document implementation with code snippets and diagrams

### 5.5 Chapter 5: Experiments (Weeks 9-11)
1. **Week 9**: Design experiments and prepare datasets
2. **Week 10**: Run effectiveness and security experiments
3. **Week 11**: Analyze results and create visualizations
4. Write experimental chapter with results

### 5.6 Chapter 6: Conclusions (Week 12)
1. Summarize contributions
2. Answer all RQs explicitly
3. Discuss limitations
4. Outline future work
5. Final review with supervisor

### 5.7 Frontmatter & Appendices (Week 13)
1. Write English abstract (max 500 words)
2. Write Portuguese abstract
3. Update acknowledgments
4. Write dedication (optional)
5. Create appendices (code listings, additional tables, full PRISMA data extraction)
6. Update glossary with all acronyms used

### 5.8 Bibliography Finalization (Week 13)
1. Verify all citations in text have references
2. Ensure consistent formatting
3. Add missing DOIs/URLs
4. Alphabetical order check

### 5.9 Final Review & Formatting (Week 14)
1. Spell check and grammar review
2. Consistency check (terminology, notation)
3. Figure and table numbering verification
4. Cross-reference validation
5. Page count check (aim for 80-100 pages excluding appendices)
6. Generate final PDF
7. Proof-read entire document

---

## Phase 6: LaTeX Implementation Checklist

### 6.1 Update main.tex Metadata
- [ ] Update `\thesissubtitle` (remove placeholder)
- [ ] Add `\cosupervisor` if applicable (or comment out)
- [ ] Update `\committeepresident` and `\committeemembers`
- [ ] Update `\university` and `\department` URLs
- [ ] Verify `\keywords` are final
- [ ] Set final `\thesisdate`

### 6.2 Create New Chapter Files
- [ ] Replace `ch1/chapter1.tex` with Introduction content
- [ ] Replace `ch2/chapter2.tex` with Literature Review content
- [ ] Replace `ch3/chapter3.tex` with Architecture content
- [ ] Create `ch4/chapter4.tex` for Implementation
- [ ] Create `ch5/chapter5.tex` for Experiments
- [ ] Create `ch6/chapter6.tex` for Conclusions
- [ ] Uncomment chapter includes in main.tex

### 6.3 Update Frontmatter
- [ ] Write `frontmatter/abstract_en.tex` (English abstract)
- [ ] Write `frontmatter/abstract_pt.tex` (Portuguese abstract)
- [ ] Update `frontmatter/glossary.tex` with all acronyms:
  - MAS, LLM, ACI, GDPR, DPIA, PRISMA, SLR, RQ, CI/CD, API
  - GPT, AST, HITL, RAG, NPE, RCE, SQLi, CTF, etc.
- [ ] Update acknowledgments section in `frontmatter/frontmatter.tex`
- [ ] Update dedication section (or remove)

### 6.4 Bibliography Management
- [ ] Clear template references from `mainbibliography.bib`
- [ ] Add all 20 PSGEIA references
- [ ] Add 25-30 additional references from extended search
- [ ] Verify BibTeX formatting
- [ ] Test compilation with `biber`

### 6.5 Assets Organization
- [ ] Create architecture diagrams (Visio, Draw.io, TikZ)
- [ ] Create PRISMA flow diagram (update with final numbers)
- [ ] Create experimental results charts (matplotlib, pgfplots)
- [ ] Add screenshots/code snippets for implementation chapter
- [ ] Organize into `chN/assets/` directories

### 6.6 Cross-References
- [ ] Label all chapters: `\label{chap:introduction}`, etc.
- [ ] Label all sections: `\label{sec:rq_definition}`, etc.
- [ ] Label all figures: `\label{fig:architecture}`, etc.
- [ ] Label all tables: `\label{tab:study_overview}`, etc.
- [ ] Label all equations: `\label{eq:coverage}`, etc.
- [ ] Use `\ref{}` and `\pageref{}` consistently

---

## Phase 7: Quality Assurance

### 7.1 Content Quality Checks
- [ ] All RQs clearly stated and answered
- [ ] PRISMA protocol rigorously followed
- [ ] Methodology clearly described and reproducible
- [ ] Results presented with appropriate statistical analysis
- [ ] Figures and tables have captions and are referenced in text
- [ ] All claims are supported by citations
- [ ] No plagiarism (use Turnitin/similarity checker)
- [ ] Ethical considerations addressed

### 7.2 LaTeX Quality Checks
- [ ] Document compiles without errors: `make`
- [ ] All citations resolved (no `?` in PDF)
- [ ] All cross-references resolved
- [ ] No overfull/underfull hbox warnings (major ones)
- [ ] Consistent formatting (font, spacing, margins)
- [ ] Page numbers correct (Roman for frontmatter, Arabic for body)
- [ ] List of Figures/Tables/Algorithms complete and accurate
- [ ] Glossary/acronyms compiled correctly

### 7.3 Academic Writing Standards
- [ ] Clear, formal academic English
- [ ] No colloquial expressions
- [ ] Consistent terminology throughout
- [ ] Proper use of past/present tense
- [ ] Active voice where appropriate
- [ ] Transitions between sections smooth
- [ ] No repetition across chapters

### 7.4 Supervisor Review Gates
- [ ] Checkpoint 1: Chapter 1 + Chapter 2 outline
- [ ] Checkpoint 2: Complete Literature Review (Chapter 2)
- [ ] Checkpoint 3: Architecture and Implementation plan (Chapters 3-4)
- [ ] Checkpoint 4: Experimental results (Chapter 5)
- [ ] Checkpoint 5: Complete draft review
- [ ] Checkpoint 6: Final version approval

---

## Key Success Factors

1. **Start with RQ Definition**: Ensure all 6 RQs are clear and approved by supervisor before proceeding
2. **Leverage Existing Work**:
   - PSGEIA paper provides ~30-40% of literature review (security/privacy focus)
   - Don't rewrite what's already done well - integrate it
3. **Follow PRISMA Rigorously**: This ensures methodological rigor and reproducibility
4. **Prototype Early**: Start implementation in parallel with literature review to identify practical challenges
5. **Regular Supervisor Meetings**: Weekly or bi-weekly check-ins to avoid major revisions late
6. **Version Control**: Use git to track all changes to LaTeX files
7. **Backup Strategy**: Regular backups to prevent data loss (cloud + local)
8. **Time Buffer**: Build in 2-3 weeks buffer before final deadline for unexpected issues

---

## Estimated Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| RQ Definition | 1 week | Approved RQ1-RQ6 |
| Extended Lit Search | 2 weeks | ~40 total papers selected |
| Chapter 1 (Intro) | 1 week | Draft introduction |
| Chapter 2 (Lit Review) | 3 weeks | Complete literature review |
| Chapter 3 (Architecture) | 1 week | Architecture design |
| Chapter 4 (Implementation) | 3 weeks | Prototype + documentation |
| Chapter 5 (Experiments) | 3 weeks | Results and analysis |
| Chapter 6 (Conclusions) | 1 week | Final synthesis |
| Frontmatter/Appendices | 1 week | Abstracts, glossary, etc. |
| Final Review & Polish | 1 week | Camera-ready version |
| **Total** | **17 weeks** | **Complete thesis** |

Add 2-3 weeks buffer for iterations and revisions → **~20 weeks (5 months) total**

---

## Next Immediate Steps

### Step 1: Define Research Questions (THIS WEEK)
1. Review the proposed RQ3-RQ6 above
2. Refine wording based on supervisor feedback
3. Ensure alignment with thesis scope and feasibility
4. Document final RQ list

### Step 2: Plan Extended Literature Search (NEXT WEEK)
1. Finalize search strings for RQ3-RQ6
2. Conduct preliminary searches in IEEE/ACM
3. Estimate number of papers to review
4. Create PRISMA screening spreadsheet

### Step 3: Start Chapter 1 Draft (NEXT WEEK)
1. Write motivation and context (can start immediately)
2. Draft problem statement
3. Outline objectives and contributions
4. Create thesis structure overview

### Step 4: Set Up Implementation Environment (PARALLEL)
1. Choose agent framework (LangChain, CrewAI, or custom)
2. Set up Docker for sandboxing
3. Configure LLM API access (OpenAI + local Llama)
4. Initialize git repository for prototype code

---

## Questions for Supervisor Review

1. **RQ Scope**: Are RQ3-RQ6 appropriately scoped for a Master's thesis, or should any be simplified/removed?
2. **Implementation Depth**: How extensive should the prototype be? Full working system or proof-of-concept?
3. **Experimental Scale**: What scale of experiments is expected? (e.g., how many benchmark projects?)
4. **Security Focus**: Should security/privacy remain a primary contribution, or shift more toward effectiveness/architecture?
5. **Timeline**: Is 5 months realistic given the current progress, or should scope be adjusted?
6. **PSGEIA Integration**: Preferred approach for integrating the already-published PSGEIA paper into the thesis?

---

## Resources and Tools

### Literature Management
- Zotero or Mendeley for reference management
- Connected Papers for citation network exploration
- Google Scholar alerts for new papers

### Writing and LaTeX
- Overleaf (online) or local TeX distribution
- Grammarly or LanguageTool for grammar checking
- Draw.io or Visio for diagrams
- Matplotlib/Seaborn for result visualization

### Implementation
- Python 3.10+
- LangChain or CrewAI for agent framework
- Docker for sandboxing
- GitHub for version control
- pytest for test generation validation

### Collaboration
- GitHub for thesis LaTeX source
- Shared Overleaf project with supervisor (optional)
- Regular meeting notes document

---

## End of Plan

**Document Version**: 1.0
**Last Updated**: 2026-02-13
**Status**: Draft for Supervisor Review
