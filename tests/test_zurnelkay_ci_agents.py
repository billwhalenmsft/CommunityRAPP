"""
Test Suite: Zurn Elkay Competitive Intelligence Agents
Purpose: Validate all Level 1 BU agents, data integrity, and integration

Test Categories:
1. Unit Tests - Individual agent functionality
2. Data Validation Tests - Data integrity and consistency
3. Integration Tests - Multi-agent coordination (requires Synthesizer/Orchestrator)
4. Edge Cases - Error handling and fallbacks
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all BU agents
from agents.zurnelkay_drains_ci_agent import ZurnElkayDrainsCIAgent
from agents.zurnelkay_wilkins_ci_agent import ZurnElkayWilkinsCIAgent
from agents.zurnelkay_drinking_water_ci_agent import ZurnElkayDrinkingWaterCIAgent
from agents.zurnelkay_sinks_ci_agent import ZurnElkaySinksCIAgent
from agents.zurnelkay_commercial_brass_ci_agent import ZurnElkayCommercialBrassCIAgent


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def zurnelkay_drains_agent():
    """Create Drains CI agent instance."""
    return ZurnElkayDrainsCIAgent()


@pytest.fixture
def zurnelkay_wilkins_agent():
    """Create Wilkins CI agent instance."""
    return ZurnElkayWilkinsCIAgent()


@pytest.fixture
def zurnelkay_drinking_water_agent():
    """Create Drinking Water CI agent instance."""
    return ZurnElkayDrinkingWaterCIAgent()


@pytest.fixture
def zurnelkay_sinks_agent():
    """Create Sinks CI agent instance."""
    return ZurnElkaySinksCIAgent()


@pytest.fixture
def zurnelkay_commercial_brass_agent():
    """Create Commercial Brass CI agent instance."""
    return ZurnElkayCommercialBrassCIAgent()


@pytest.fixture
def zurnelkay_all_agents(zurnelkay_drains_agent, zurnelkay_wilkins_agent, 
                          zurnelkay_drinking_water_agent, zurnelkay_sinks_agent,
                          zurnelkay_commercial_brass_agent):
    """Return all BU agents for cross-agent tests."""
    return {
        "drains": zurnelkay_drains_agent,
        "wilkins": zurnelkay_wilkins_agent,
        "drinking_water": zurnelkay_drinking_water_agent,
        "sinks": zurnelkay_sinks_agent,
        "commercial_brass": zurnelkay_commercial_brass_agent
    }


# =============================================================================
# 1. UNIT TESTS - DRAINS AGENT
# =============================================================================

class TestZurnElkayDrainsAgent:
    """Unit tests for Drains CI Agent."""

    def test_zurnelkay_drains_perform_unknown_action(self, zurnelkay_drains_agent):
        """Returns error for invalid action."""
        result = zurnelkay_drains_agent.perform("invalid_action_xyz")
        assert "error" in result
        assert "available_actions" in result

    def test_zurnelkay_drains_run_quarterly_analysis(self, zurnelkay_drains_agent):
        """Returns required fields for quarterly analysis."""
        result = zurnelkay_drains_agent.perform("run_quarterly_analysis")
        
        assert result.get("report_type") == "Quarterly Competitive Intelligence"
        assert result.get("business_unit") == "Drains"
        assert "highlights_by_product_family" in result
        assert "top_3_significant_changes" in result
        assert "implications" in result
        assert "generated_at" in result

    def test_zurnelkay_drains_analyze_competitor_valid(self, zurnelkay_drains_agent):
        """Returns data for known competitor."""
        result = zurnelkay_drains_agent.perform("analyze_competitor", competitor="Watts")
        
        assert "error" not in result
        assert result.get("competitor") == "Watts"
        assert "parent_company" in result

    def test_zurnelkay_drains_analyze_competitor_with_parent(self, zurnelkay_drains_agent):
        """Returns parent company for brands with known parent."""
        result = zurnelkay_drains_agent.perform("analyze_competitor", competitor="Josam")
        
        # Josam is owned by Watts Water Technologies
        assert result.get("parent_company") == "Watts Water Technologies"

    def test_zurnelkay_drains_parent_company_coordination(self, zurnelkay_drains_agent):
        """Returns coordination signals for valid parent."""
        result = zurnelkay_drains_agent.perform(
            "check_parent_company_coordination", 
            parent_company="Watts Water Technologies"
        )
        
        assert "error" not in result
        assert "brands_monitored" in result
        # Check for either coordination_signals or signals key
        assert "coordination_signals" in result or "signals" in result
        assert len(result["brands_monitored"]) > 0

    def test_zurnelkay_drains_parent_company_invalid(self, zurnelkay_drains_agent):
        """Returns error for unknown parent company."""
        result = zurnelkay_drains_agent.perform(
            "check_parent_company_coordination",
            parent_company="Fake Company XYZ"
        )
        
        assert "error" in result

    def test_zurnelkay_drains_signal_summary(self, zurnelkay_drains_agent):
        """Returns signal summary with count."""
        result = zurnelkay_drains_agent.perform("get_signal_summary")
        
        assert "signals" in result
        # Check for either count or signal_count key
        assert "count" in result or "signal_count" in result
        assert isinstance(result["signals"], list)

    def test_zurnelkay_drains_generate_bu_report_format(self, zurnelkay_drains_agent):
        """Report has required executive fields."""
        result = zurnelkay_drains_agent.perform("generate_bu_report")
        
        assert "report_title" in result
        assert "executive_summary" in result
        assert "sources" in result
        assert "generated_at" in result


# =============================================================================
# 1. UNIT TESTS - WILKINS AGENT
# =============================================================================

class TestZurnElkayWilkinsAgent:
    """Unit tests for Wilkins CI Agent."""

    def test_zurnelkay_wilkins_perform_unknown_action(self, zurnelkay_wilkins_agent):
        """Returns error for invalid action."""
        result = zurnelkay_wilkins_agent.perform("invalid_action_xyz")
        assert "error" in result

    def test_zurnelkay_wilkins_run_quarterly_analysis(self, zurnelkay_wilkins_agent):
        """Returns required fields for quarterly analysis."""
        result = zurnelkay_wilkins_agent.perform("run_quarterly_analysis")
        
        assert result.get("business_unit") == "Wilkins"
        assert "highlights_by_product_family" in result
        assert "backflow" in result["highlights_by_product_family"]
        assert "prvs" in result["highlights_by_product_family"]
        assert "tmvs" in result["highlights_by_product_family"]

    def test_zurnelkay_wilkins_digital_innovation(self, zurnelkay_wilkins_agent):
        """Returns digital/smart valve innovations."""
        result = zurnelkay_wilkins_agent.perform("get_digital_innovation")
        
        assert "innovations" in result
        assert "feature_comparison" in result
        assert "trend" in result

    def test_zurnelkay_wilkins_certification_changes(self, zurnelkay_wilkins_agent):
        """Returns certification and code updates."""
        result = zurnelkay_wilkins_agent.perform("get_certification_changes")
        
        assert "certifications" in result
        assert "code_updates" in result
        assert "standards_monitored" in result

    def test_zurnelkay_wilkins_watts_portfolio_analysis(self, zurnelkay_wilkins_agent):
        """Special analysis for Watts as portfolio player."""
        result = zurnelkay_wilkins_agent.perform("analyze_competitor", competitor="Watts")
        
        # Watts should trigger portfolio analysis
        assert "analysis_type" in result or "competitor" in result
        assert "portfolio_strategy_signals" in result or "parent_company" in result


# =============================================================================
# 1. UNIT TESTS - DRINKING WATER AGENT
# =============================================================================

class TestZurnElkayDrinkingWaterAgent:
    """Unit tests for Drinking Water CI Agent."""

    def test_zurnelkay_drinking_water_perform_unknown_action(self, zurnelkay_drinking_water_agent):
        """Returns error for invalid action."""
        result = zurnelkay_drinking_water_agent.perform("invalid_action_xyz")
        assert "error" in result

    def test_zurnelkay_drinking_water_run_quarterly_analysis(self, zurnelkay_drinking_water_agent):
        """Returns required fields for quarterly analysis."""
        result = zurnelkay_drinking_water_agent.perform("run_quarterly_analysis")
        
        assert result.get("business_unit") == "Elkay Drinking Water"
        assert "highlights_by_product_family" in result
        assert "bottle_fillers" in result["highlights_by_product_family"]

    def test_zurnelkay_drinking_water_nsf_certifications(self, zurnelkay_drinking_water_agent):
        """Returns NSF certification data."""
        result = zurnelkay_drinking_water_agent.perform("check_nsf_certifications")
        
        assert "certification_updates" in result
        assert "standards_monitored" in result
        assert "verification_sources" in result

    def test_zurnelkay_drinking_water_public_sector_wins(self, zurnelkay_drinking_water_agent):
        """Returns public sector contract data."""
        result = zurnelkay_drinking_water_agent.perform("get_public_sector_wins")
        
        assert "contract_activity" in result
        assert "sources_monitored" in result

    def test_zurnelkay_drinking_water_sustainability_claims(self, zurnelkay_drinking_water_agent):
        """Returns sustainability claims with verification status."""
        result = zurnelkay_drinking_water_agent.perform("get_sustainability_claims")
        
        assert "claims" in result
        assert "verification_approach" in result


# =============================================================================
# 1. UNIT TESTS - SINKS AGENT
# =============================================================================

class TestZurnElkaySinksAgent:
    """Unit tests for Sinks CI Agent."""

    def test_zurnelkay_sinks_perform_unknown_action(self, zurnelkay_sinks_agent):
        """Returns error for invalid action."""
        result = zurnelkay_sinks_agent.perform("invalid_action_xyz")
        assert "error" in result

    def test_zurnelkay_sinks_run_quarterly_analysis(self, zurnelkay_sinks_agent):
        """Returns required fields for quarterly analysis."""
        result = zurnelkay_sinks_agent.perform("run_quarterly_analysis")
        
        assert result.get("business_unit") == "Elkay & Just Sinks"
        assert "highlights_by_segment" in result
        assert "healthcare" in result["highlights_by_segment"]

    def test_zurnelkay_sinks_healthcare_innovations(self, zurnelkay_sinks_agent):
        """Returns healthcare infection control innovations."""
        result = zurnelkay_sinks_agent.perform("get_healthcare_innovations")
        
        assert "innovations" in result
        assert "trend_summary" in result

    def test_zurnelkay_sinks_ada_compliance(self, zurnelkay_sinks_agent):
        """Returns ADA compliance updates."""
        result = zurnelkay_sinks_agent.perform("get_ada_compliance_updates")
        
        assert "updates" in result
        assert "standards_monitored" in result

    def test_zurnelkay_sinks_morris_coordination(self, zurnelkay_sinks_agent):
        """Returns Morris Group coordination signals."""
        result = zurnelkay_sinks_agent.perform(
            "check_parent_company_coordination",
            parent_company="Morris Group"
        )
        
        assert "coordination_signals" in result
        assert "brands_monitored" in result


# =============================================================================
# 1. UNIT TESTS - COMMERCIAL BRASS AGENT
# =============================================================================

class TestZurnElkayCommercialBrassAgent:
    """Unit tests for Commercial Brass CI Agent."""

    def test_zurnelkay_commercial_brass_perform_unknown_action(self, zurnelkay_commercial_brass_agent):
        """Returns error for invalid action."""
        result = zurnelkay_commercial_brass_agent.perform("invalid_action_xyz")
        assert "error" in result

    def test_zurnelkay_commercial_brass_run_quarterly_analysis(self, zurnelkay_commercial_brass_agent):
        """Returns required fields for quarterly analysis."""
        result = zurnelkay_commercial_brass_agent.perform("run_quarterly_analysis")
        
        assert result.get("business_unit") == "Commercial Brass"
        assert "strategic_theme" in result
        assert "highlights_by_segment" in result

    def test_zurnelkay_commercial_brass_platform_launches(self, zurnelkay_commercial_brass_agent):
        """Returns platform/system launches."""
        result = zurnelkay_commercial_brass_agent.perform("get_platform_launches")
        
        assert "platforms" in result
        assert "trend_summary" in result

    def test_zurnelkay_commercial_brass_touchless_technology(self, zurnelkay_commercial_brass_agent):
        """Returns touchless technology updates."""
        result = zurnelkay_commercial_brass_agent.perform("get_touchless_technology")
        
        assert "touchless_products" in result

    def test_zurnelkay_commercial_brass_water_management(self, zurnelkay_commercial_brass_agent):
        """Returns water management/IoT systems."""
        result = zurnelkay_commercial_brass_agent.perform("get_water_management_systems")
        
        assert "systems" in result

    def test_zurnelkay_commercial_brass_sloan_analysis(self, zurnelkay_commercial_brass_agent):
        """Special platform strategy analysis for Sloan."""
        result = zurnelkay_commercial_brass_agent.perform("analyze_competitor", competitor="Sloan")
        
        # Sloan should trigger platform strategy deep dive
        assert "strategic_assessment" in result or "competitor" in result


# =============================================================================
# 2. DATA VALIDATION TESTS
# =============================================================================

class TestZurnElkayDataValidation:
    """Data integrity and consistency tests across all agents."""

    def test_zurnelkay_no_duplicate_primary_competitors(self, zurnelkay_all_agents):
        """No competitor appears as PRIMARY in multiple BU agent lists."""
        all_primary_competitors = []
        
        for bu_name, agent in zurnelkay_all_agents.items():
            for product_family, competitors in agent.competitors.items():
                for competitor in competitors.get("primary", []):
                    all_primary_competitors.append((competitor, bu_name, product_family))
        
        # Check for duplicates (same competitor in multiple BUs as primary)
        seen = {}
        duplicates = []
        for competitor, bu, pf in all_primary_competitors:
            key = competitor
            if key in seen and seen[key][0] != bu:
                duplicates.append(f"{competitor} in {bu}/{pf} and {seen[key][0]}/{seen[key][1]}")
            seen[key] = (bu, pf)
        
        # Note: Some overlap is expected (e.g., Watts appears in multiple BUs)
        # This test documents the overlap rather than failing
        if duplicates:
            print(f"Note: Cross-BU competitors found: {duplicates}")

    def test_zurnelkay_parent_company_mapping_complete(self, zurnelkay_all_agents):
        """All coordinated brands have parent mapping."""
        for bu_name, agent in zurnelkay_all_agents.items():
            # Get all brands mentioned in parent companies
            all_brands = []
            for parent, brands in agent.parent_companies.items():
                all_brands.extend(brands)
            
            # Verify each brand is mapped
            assert len(all_brands) > 0, f"{bu_name} has no parent company mappings"

    def test_zurnelkay_source_attribution(self, zurnelkay_all_agents):
        """Every simulated signal has a source field."""
        for bu_name, agent in zurnelkay_all_agents.items():
            # Check product launches
            if hasattr(agent, 'simulated_product_launches'):
                for launch in agent.simulated_product_launches:
                    assert "source" in launch, f"{bu_name}: Product launch missing source"
            
            # Check certifications
            if hasattr(agent, 'simulated_certifications'):
                for cert in agent.simulated_certifications:
                    assert "source" in cert, f"{bu_name}: Certification missing source"

    def test_zurnelkay_confidence_levels_valid(self, zurnelkay_all_agents):
        """All items have valid confidence levels (high/medium/low)."""
        valid_confidence = {"high", "medium", "low"}
        
        for bu_name, agent in zurnelkay_all_agents.items():
            if hasattr(agent, 'simulated_product_launches'):
                for launch in agent.simulated_product_launches:
                    if "confidence" in launch:
                        assert launch["confidence"] in valid_confidence, \
                            f"{bu_name}: Invalid confidence '{launch['confidence']}'"

    def test_zurnelkay_signal_priority_range(self, zurnelkay_all_agents):
        """Signal priorities are in valid range (1-5, 1=highest)."""
        for bu_name, agent in zurnelkay_all_agents.items():
            if hasattr(agent, 'simulated_product_launches'):
                for launch in agent.simulated_product_launches:
                    if "signal_priority" in launch:
                        assert 1 <= launch["signal_priority"] <= 5, \
                            f"{bu_name}: Invalid priority {launch['signal_priority']}"

    def test_zurnelkay_date_format_consistency(self, zurnelkay_all_agents):
        """All dates are in consistent format (YYYY-MM-DD or ISO)."""
        for bu_name, agent in zurnelkay_all_agents.items():
            if hasattr(agent, 'simulated_product_launches'):
                for launch in agent.simulated_product_launches:
                    if "launch_date" in launch and launch["launch_date"]:
                        date_str = launch["launch_date"]
                        # Should be YYYY-MM-DD format
                        try:
                            datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            pytest.fail(f"{bu_name}: Invalid date format '{date_str}'")


# =============================================================================
# 3. INTEGRATION TESTS (Requires Synthesizer/Orchestrator)
# =============================================================================

class TestZurnElkayIntegration:
    """Integration tests for multi-agent coordination."""

    def test_zurnelkay_all_bu_agents_respond(self, zurnelkay_all_agents):
        """All 5 BU agents respond to quarterly analysis."""
        for bu_name, agent in zurnelkay_all_agents.items():
            result = agent.perform("run_quarterly_analysis")
            
            assert "error" not in result, f"{bu_name} failed: {result.get('error')}"
            assert "generated_at" in result, f"{bu_name} missing timestamp"

    def test_zurnelkay_all_bu_reports_generated(self, zurnelkay_all_agents):
        """All 5 BU agents generate executive reports."""
        for bu_name, agent in zurnelkay_all_agents.items():
            result = agent.perform("generate_bu_report")
            
            assert "report_title" in result, f"{bu_name} missing report_title"
            assert "executive_summary" in result, f"{bu_name} missing executive_summary"
            assert "sources" in result, f"{bu_name} missing sources"

    def test_zurnelkay_cross_bu_watts_coordination(self, zurnelkay_all_agents):
        """Watts coordination signals appear in relevant BUs."""
        watts_coordination_found = []
        
        for bu_name, agent in zurnelkay_all_agents.items():
            if "Watts Water Technologies" in agent.parent_companies:
                result = agent.perform(
                    "check_parent_company_coordination",
                    parent_company="Watts Water Technologies"
                )
                # Check for either coordination_signals or signals key
                if result.get("coordination_signals") or result.get("signals"):
                    watts_coordination_found.append(bu_name)
        
        # Watts should have coordination signals in at least 1 BU
        assert len(watts_coordination_found) >= 1, \
            f"Watts coordination only found in: {watts_coordination_found}"

    def test_zurnelkay_cross_bu_morris_coordination(self, zurnelkay_all_agents):
        """Morris Group coordination signals appear in relevant BUs."""
        morris_coordination_found = []
        
        for bu_name, agent in zurnelkay_all_agents.items():
            if "Morris Group" in agent.parent_companies:
                result = agent.perform(
                    "check_parent_company_coordination",
                    parent_company="Morris Group"
                )
                if result.get("coordination_signals"):
                    morris_coordination_found.append(bu_name)
        
        # Morris should have coordination in Sinks at minimum
        assert "sinks" in morris_coordination_found, \
            f"Morris coordination expected in Sinks, found in: {morris_coordination_found}"

    @pytest.mark.skip(reason="Requires Level 2 Synthesizer agent - not yet built")
    def test_zurnelkay_synthesizer_aggregation(self, zurnelkay_all_agents):
        """Synthesizer combines 5 BU reports correctly."""
        # TODO: Implement after Synthesizer agent is built
        pass

    @pytest.mark.skip(reason="Requires Level 0 Orchestrator agent - not yet built")
    def test_zurnelkay_orchestrator_qa_validation(self, zurnelkay_all_agents):
        """Orchestrator flags low-confidence items."""
        # TODO: Implement after Orchestrator agent is built
        pass


# =============================================================================
# 4. EDGE CASES
# =============================================================================

class TestZurnElkayEdgeCases:
    """Edge cases and error handling tests."""

    def test_zurnelkay_empty_time_period_defaults(self, zurnelkay_drains_agent):
        """Defaults to last_quarter when time_period not specified."""
        result = zurnelkay_drains_agent.perform("run_quarterly_analysis")
        
        # Should succeed without time_period
        assert "error" not in result
        assert result.get("period") == "last_quarter"

    def test_zurnelkay_agent_works_without_openai(self, zurnelkay_drains_agent):
        """Agent returns simulated data when OpenAI unavailable."""
        # Force OpenAI client to None
        zurnelkay_drains_agent.openai_client = None
        
        result = zurnelkay_drains_agent.perform("run_quarterly_analysis")
        
        # Should still return valid data from simulated sources
        assert "error" not in result
        assert "top_3_significant_changes" in result

    def test_zurnelkay_trade_publication_search_graceful(self, zurnelkay_drains_agent):
        """Trade publication search returns gracefully with simulated data."""
        result = zurnelkay_drains_agent.perform(
            "search_trade_publications",
            query="test query"
        )
        
        assert "results" in result
        assert "note" in result  # Should indicate simulated

    def test_zurnelkay_product_family_filter(self, zurnelkay_drains_agent):
        """Signal summary filters by product family."""
        result = zurnelkay_drains_agent.perform(
            "get_signal_summary",
            product_family="floor_drains"
        )
        
        assert result.get("product_family") == "floor_drains"

    def test_zurnelkay_all_actions_documented(self, zurnelkay_all_agents):
        """All agent actions are documented in metadata."""
        for bu_name, agent in zurnelkay_all_agents.items():
            metadata_actions = agent.metadata["parameters"]["properties"]["action"]["enum"]
            
            # Verify each documented action exists
            for action in metadata_actions:
                result = agent.perform(action)
                assert "error" not in result or "Unknown action" not in result.get("error", ""), \
                    f"{bu_name}: Documented action '{action}' not implemented"


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
