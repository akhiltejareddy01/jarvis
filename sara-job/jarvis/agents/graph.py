"""The daily pipeline (Scout's output onward) wired as a real LangGraph graph,
per Sara_Job_Arch.docx build order — not just scripts called back-to-back.
Each node processes its full batch of pending jobs in one step rather than one
graph run per job; that keeps LangGraph's per-invocation overhead sane for a
100-150 jobs/day batch while still making the pipeline an explicit,
inspectable graph: JD Parser -> Fit Scorer -> Resume Selector -> Cover Letter.

Run:  python -m jarvis.agents.graph
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from jarvis.agents.cover_letter import run_cover_letter
from jarvis.agents.fit_scorer import run_fit_scorer
from jarvis.agents.jd_parser import run_jd_parser
from jarvis.agents.resume_selector import run_resume_selector


class PipelineState(TypedDict, total=False):
    jd_parser_result: dict
    fit_scorer_result: dict
    resume_selector_result: dict
    cover_letter_result: dict


def jd_parser_node(state: PipelineState) -> PipelineState:
    return {"jd_parser_result": run_jd_parser()}


def fit_scorer_node(state: PipelineState) -> PipelineState:
    return {"fit_scorer_result": run_fit_scorer()}


def resume_selector_node(state: PipelineState) -> PipelineState:
    return {"resume_selector_result": run_resume_selector()}


def cover_letter_node(state: PipelineState) -> PipelineState:
    return {"cover_letter_result": run_cover_letter()}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("jd_parser", jd_parser_node)
    graph.add_node("fit_scorer", fit_scorer_node)
    graph.add_node("resume_selector", resume_selector_node)
    graph.add_node("cover_letter", cover_letter_node)
    graph.set_entry_point("jd_parser")
    graph.add_edge("jd_parser", "fit_scorer")
    graph.add_edge("fit_scorer", "resume_selector")
    graph.add_edge("resume_selector", "cover_letter")
    graph.add_edge("cover_letter", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    # LangGraph's implicit START node requires the initial write to touch at
    # least one declared state key — an empty {} trips InvalidUpdateError.
    result = app.invoke({
        "jd_parser_result": {},
        "fit_scorer_result": {},
        "resume_selector_result": {},
        "cover_letter_result": {},
    })
    print(result)
