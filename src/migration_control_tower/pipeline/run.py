"""End-to-end eligibility decisioning pipeline."""

from migration_control_tower.agent import EligibilityReviewAgent
from migration_control_tower.context import ContextAssembler
from migration_control_tower.decision import DecisionCombiner
from migration_control_tower.domain.enums import RulesOutcome
from migration_control_tower.domain.models import AgentReviewResult
from migration_control_tower.micc import MiCCStub
from migration_control_tower.pipeline.result import PipelineRunResult
from migration_control_tower.rules import RulesEngine


class EligibilityPipeline:
    """Run the full control tower flow for one subscriber."""

    def __init__(
        self,
        assembler: ContextAssembler | None = None,
        rules_engine: RulesEngine | None = None,
        agent: EligibilityReviewAgent | None = None,
        combiner: DecisionCombiner | None = None,
        micc: MiCCStub | None = None,
    ) -> None:
        self.assembler = assembler or ContextAssembler()
        self.rules_engine = rules_engine or RulesEngine()
        self.agent = agent or EligibilityReviewAgent()
        self.combiner = combiner or DecisionCombiner()
        self.micc = micc or MiCCStub()

    def run(self, subscriber_id: str) -> PipelineRunResult:
        context = self.assembler.assemble(subscriber_id)
        rules_result = self.rules_engine.evaluate(context)

        agent_result: AgentReviewResult | None = None
        if rules_result.outcome == RulesOutcome.AMBIGUOUS:
            agent_result = self.agent.review(context, rules_result)

        decision = self.combiner.combine(context, rules_result, agent_result)
        execution = self.micc.submit(decision)

        return PipelineRunResult(
            subscriber_id=subscriber_id,
            context=context,
            rules_result=rules_result,
            agent_result=agent_result,
            decision=decision,
            execution=execution,
        )
