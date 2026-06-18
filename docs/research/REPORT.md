# Research Report: Dating, Attraction, Compatibility & Lasting Marriage

This report synthesizes peer-reviewed psychology, relationship science, meta-analyses, and practitioner perspectives to answer the core questions of the matchmaker-council's research brief. It concludes with concrete implications for the matchmaker design, grounding the findings in the system's existing agents, labels, and ROADMAP priorities.

## 1. What Predicts Relationship Satisfaction and Stability?

Relationship science has historically struggled to identify reliable predictors of relationship quality before two people meet, but it has robustly identified the factors that sustain a relationship once it begins. In a landmark machine-learning study analyzing 43 longitudinal datasets of over 11,000 couples, researchers found that relationship-specific, perceptual variables dominate the prediction of relationship quality [1]. The top predictors were perceived partner commitment, appreciation, sexual satisfaction, perceived partner satisfaction, and conflict [1]. Notably, actor-reported variables (how one perceives the relationship) predicted two to four times more variance than partner-reported variables (the partner's own traits or perceptions), and individual differences alone offered little predictive power beyond the relationship-specific experience [1].

In terms of stability and divorce prediction, the field must balance descriptive insights with predictive humility. While John Gottman’s identification of the "Four Horsemen" (criticism, contempt, defensiveness, and stonewalling) and the importance of repair attempts remain foundational descriptive constructs of relationship distress [2], claims that these behaviors can prospectively predict divorce with over 90% accuracy have been strongly critiqued. Re-analyses demonstrate that such high accuracy rates were the result of overfitting small samples and extreme groups; when adjusted for base rates and cross-validated, the positive predictive value of these models drops precipitously [3]. The core takeaway is that while toxic conflict patterns are dangerous, accurately forecasting *which* specific couples will ultimately divorce remains highly uncertain.

## 2. Attraction: Fixed or Cultivable?

The evidence strongly supports the view that attraction is cultivable rather than fixed. While initial physical spark matters, repeated positive interaction significantly deepens attraction. A study of live interactions between strangers demonstrated that the more individuals interacted, the more attracted they became, mediated by perceived responsiveness, comfort, and perceived knowledge [4]. This counters the "familiarity breeds contempt" hypothesis, which primarily applies to decontextualized trait lists rather than live human connection.

Furthermore, stated ideal partner preferences have remarkably little predictive validity for who individuals actually desire after meeting face-to-face [5]. In speed-dating contexts, machine learning models could predict an individual's general tendency to desire others (actor variance) or to be desired (partner variance), but they were entirely unable to predict compatibility with a specific partner (relationship variance) based on pre-date trait questionnaires [6]. Attraction is an emergent property of interaction, not a checklist of traits.

## 3. Compatibility: Values, Goals, and the Limits of Similarity

Matching algorithms that rely on pre-acquaintance demographic or attitudinal similarity are fundamentally limited. A critical review of the online dating industry concluded that there is "no compelling evidence that any matching algorithm works" better than chance [7]. These algorithms rely on principles like similarity and complementarity that are far less important to long-term relationship well-being than interaction dynamics and shared growth [7]. 

However, while surface-level similarity is overrated, deep value and goal congruence are highly protective. Value congruence and goal congruence predict higher marital quality and lower odds of divorce [8]. Specifically, shared religious involvement and intrafaith marriage are associated with significantly higher relationship stability, largely due to shared values, community support, and the sanctification of the marriage [9]. Conversely, religious heterogamy (mismatched faith) is associated with higher instability [9].

## 4. Emotional Maturity, Repair, and Growth Beliefs

The capacity to repair after conflict and the willingness to grow are critical determinants of long-term success. Attachment theory provides a robust framework for understanding emotional maturity. The Temporal Adult Romantic Attachment (TARA) model demonstrates that the negative effects of insecure attachment (both anxious and avoidant) on relationship satisfaction and commitment actually *worsen* as the relationship duration increases [10]. This highlights that emotional immaturity or avoidant patterns that seem manageable early on can severely corrode a marriage over time.

However, low emotional maturity is not necessarily a permanent sentence; it can be improved. Implicit theories of relationships play a major role here. Individuals with "growth beliefs" (the assumption that relationships require effort and cultivation) cope more constructively with challenges and persist longer than those with "destiny beliefs" (the assumption that partners are either meant to be or not) [11]. 

## 5. The Role of External Support

External support systems, including therapy and premarital education, show measurable positive effects on relationship skills and satisfaction. Emotionally Focused Therapy (EFT), which specifically targets attachment bonds and repair capacity, has been shown in meta-analyses to produce large, sustained improvements in marital satisfaction, with approximately 70% of couples becoming symptom-free [12]. 

Premarital relationship education (such as the PREP program) also demonstrates moderate positive effects on communication and short-term satisfaction, though its long-term ability to prevent divorce is more mixed and depends heavily on the couples' baseline risk [13]. Retrospective interviews with divorced individuals who completed premarital education reveal that the most common reasons for their eventual divorce were lack of commitment, infidelity, and severe conflict—suggesting that education must be paired with genuine commitment and safety to be effective [14].

## 6. Trust and Safety: Gates vs. Workable Issues

The literature draws a sharp line between areas for growth and fundamental safety gates. Self-concealment from a partner is not merely a communication quirk; it is actively associated with lower relationship satisfaction and commitment, driven by thwarted basic needs for autonomy and relatedness [15]. Daily concealment predicts lower well-being the following day, and one partner's concealment harms the other's well-being [15]. 

Similarly, the demand-withdraw pattern (where one partner pursues and the other stonewalls) is a robust predictor of distress and divorce [2]. When looking at the "final straw" reasons for divorce, intimate partner violence, untreated substance abuse, and infidelity consistently top the list [14]. These are structural safety gates that cannot be overcome by strong "on-paper" compatibility or mere hope.

## 7. Implications for the Matchmaker Design

The research findings validate several core intuitions encoded in the matchmaker-council while challenging others. Below are the concrete implications mapped to the existing agents, labels, and the ROADMAP priorities.

**Confirming the Council's Architecture**
*   **AttractionSpark:** The finding that attraction is emergent and cultivable [4] [6] strongly supports the GRACE_CLAUSE instruction to treat low spark as cultivable over time. The system correctly identifies that surface-level attraction can deepen as character is revealed.
*   **ValuesFaith:** The literature confirms that while demographic similarity is overrated [7], core value and faith congruence are highly protective [8] [9]. This validates `ValuesFaith` as a Layer 1 compatibility agent that correctly flags mismatched timelines or core beliefs (as seen in the `Maya & Daniel` pair).
*   **EmotionalPatternFit & RealityCheck:** The TARA model [10] and self-concealment research [15] confirm that avoidant patterns and non-disclosure are corrosive over time. This perfectly validates the `Noah & Grace` label (`conditional_no`), where an undisclosed avoidant pattern undermines trust and safety, and validates the `RealityCheck` agent's charter to flag non-disclosure and over-functioning.

**Refining the Agents and Labels**
*   **Scope the Skeptic (ROADMAP Priority):** The experiment report (`report.md`) showed that the `grace_skeptic` stance was overly harsh on ambiguous pairs, crushing nuance. The research on predictive humility [3] supports the ROADMAP goal to scope `RealityCheck` strictly to trust/safety gates (abuse, concealment, severe withdrawal) rather than allowing it to veto all ambiguity. The system must accept that relationship variance is inherently unpredictable [6], and ambiguity should yield a calibrated `conditional` verdict, not a skeptical veto.
*   **WillingnessToGrow:** The research on growth vs. destiny beliefs [11] strongly supports the `WillingnessToGrow` agent. However, to align with the EFT [12] and PREP [13] findings, this agent should explicitly look for *demonstrated actions* toward growth (e.g., seeking counsel, accountability) rather than just stated intentions, as stated preferences are often poor predictors of actual behavior [5].
*   **External Support as a First-Class Field (ROADMAP Priority):** The evidence that shared faith [9] and structured therapy [12] significantly alter relationship trajectories supports the open design question to elevate "external support" to a first-class profile field. `EmotionalMaturity` currently relies on this via the GRACE_CLAUSE, but giving the agents structured data on a pair's community and mentorship would ground their optimism in empirical reality rather than abstract hope.

**Addressing Calibration (ROADMAP Priority)**
*   The headline weakness identified in the `v0-checkpoint` is overconfidence on ambiguous pairs (e.g., `Ade & Joy`). The critique of divorce prediction models [3] and the machine learning speed-dating study [6] both emphasize extreme predictive humility: we cannot reliably forecast exactly who will succeed. The `Judge` prompt must be updated to explicitly reward wide confidence bands and penalize false certainty when predicting outcomes based on pre-acquaintance profiles. 

## References

[1] Joel, S., Eastwick, P. W., et al. (2020). Machine learning uncovers the most robust self-report predictors of relationship quality across 43 longitudinal couples studies. *Proceedings of the National Academy of Sciences*, 117(32), 19061-19071. https://www.pnas.org/doi/10.1073/pnas.1917036117
[2] Gottman, J. M., et al. (1998). Predicting marital happiness and stability from newlywed interactions. *Journal of Marriage and the Family*, 60(1), 5-22.
[3] Heyman, R. E., & Smith Slep, A. M. (2001). The Hazards of Predicting Divorce Without Crossvalidation. *Journal of Marriage and Family*, 63(2), 473-479. https://pmc.ncbi.nlm.nih.gov/articles/PMC1622921/
[4] Reis, H. T., et al. (2011). Familiarity does indeed promote attraction in live interaction. *Journal of Personality and Social Psychology*, 101(3), 557-570.
[5] Eastwick, P. W., Luchies, L. B., Finkel, E. J., & Hunt, L. L. (2014). The predictive validity of ideal partner preferences: A review and meta-analysis. *Psychological Bulletin*, 140(3), 623-665.
[6] Joel, S., Eastwick, P. W., & Finkel, E. J. (2017). Is Romantic Desire Predictable? Machine Learning Applied to Initial Romantic Attraction. *Psychological Science*, 28(10), 1478-1489. https://journals.sagepub.com/doi/abs/10.1177/0956797617714580
[7] Finkel, E. J., Eastwick, P. W., Karney, B. R., Reis, H. T., & Sprecher, S. (2012). Online Dating: A Critical Analysis From the Perspective of Psychological Science. *Psychological Science in the Public Interest*, 13(1), 3-66. https://faculty.wcas.northwestern.edu/eli-finkel/documents/2012_FinkelEastwickKarneyReisSprecher_PSPI.pdf
[8] Value congruence, goal congruence, and conflict as predictors of early marital disruption. (n.d.). Kansas State University.
[9] Boulis, A. (2024). Religion as a Determinant of Relationship Stability. *Journal for the Scientific Study of Religion*.
[10] Hadden, B. W., Smith, C. V., & Webster, G. D. (2014). Relationship duration moderates associations between attachment and relationship quality: meta-analytic support for the temporal adult romantic attachment model. *Personality and Social Psychology Review*, 18(1), 42-58. https://pubmed.ncbi.nlm.nih.gov/24026179/
[11] Knee, C. R. (1998). Implicit theories of relationships: Assessment and prediction of romantic relationship initiation, coping, and longevity. *Journal of Personality and Social Psychology*, 74(2), 360-370.
[12] Spengler, P. M., et al. (2024). A comprehensive meta-analysis on the efficacy of emotionally focused couple therapy. *Couple and Family Psychology*.
[13] Hawkins, A. J., et al. (2008). Does marriage and relationship education work? A meta-analytic study. *Journal of Consulting and Clinical Psychology*, 76(5), 723-734.
[14] Scott, S. B., et al. (2013). Reasons for Divorce and Recollections of Premarital Intervention: Implications for Improving Relationship Education. *Couple and Family Psychology*, 2(2), 131-145. https://pmc.ncbi.nlm.nih.gov/articles/PMC4012696/
[15] Uysal, A., Lin, H. L., Knee, C. R., & Bush, A. L. (2012). The association between self-concealment from one's partner and relationship well-being. *Personality and Social Psychology Bulletin*, 38(1), 39-51. https://pubmed.ncbi.nlm.nih.gov/22109250/
