from pathlib import Path
import os
import anthropic
import DataBase.db as db

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def build_series_intent_prompt(question):
    with open(PROMPTS_DIR / "planner/series_intent.txt") as f:
        template = f.read()
        prompt = template.format(question=question)
    return prompt    

def build_clarification_prompt(original_question,analysis_response,follow_up_question):
    with open(PROMPTS_DIR / "clarification_prompt.txt") as f:
        template = f.read()
        prompt = template.format(original_question=original_question,analysis_response=analysis_response,follow_up_question=follow_up_question)
    return prompt    

def build_followup_prompt(chat_history,current_user_question):
    with open(PROMPTS_DIR / "followup_prompt.txt") as f:
        template = f.read()
        prompt = template.format(chat_history=chat_history,current_user_question=current_user_question)
    return prompt    

def build_conversation_action_prompt(user_input,chat_history):
    with open(PROMPTS_DIR / "conversation_action_prompt.txt") as f:
        template = f.read()
        prompt = template.format(user_input=user_input,chat_history=chat_history)
    return prompt

def build_pearson_correlation_analysis_prompt(question,context,corr_df,stats_df):
    with open(PROMPTS_DIR / "pearson_correlation_analysis_prompt.txt") as f:
        template = f.read()

        prompt = template.format(question=question,context=context,corr_df=corr_df,stats_df=stats_df)
    return prompt

def build_spearman_correlation_analysis_prompt(question,context,corr_df,stats_df,spearman_reason):
    with open(PROMPTS_DIR / "spearman_correlation_analysis_prompt.txt") as f:
        template = f.read()

        prompt = template.format(spearman_reason=spearman_reason,question=question,context=context,corr_df=corr_df,stats_df=stats_df)
    return prompt

def build_ranking_analysis_prompt(question,context,df,ranked_df,sort_field,ascending,n,aggregation_method,group_by):
    with open(PROMPTS_DIR / "ranking_analysis_prompt.txt") as f:
        template = f.read()
        prompt = template.format(question=question,
                                 df=df,
                                 context=context,
                                 ranked_df=ranked_df,
                                 sort_field=sort_field,
                                 ascending=ascending,
                                 n=n,
                                 aggregation_method=aggregation_method,
                                 group_by=group_by)
    return prompt

def build_ranking_method_prompt(question,series_semantics):
    with open(PROMPTS_DIR / "ranking_method_prompt.txt") as f:
        template = f.read()

        prompt = template.format(question=question,series_semantics=series_semantics)
    return prompt

def build_comparison_method_prompt(question,date_grain,num_groups,routing_priority,stat_test_plan):
    with open(PROMPTS_DIR / "comparison_method_prompt.txt") as f:
        template = f.read()  
        prompt = template.format(date_grain=date_grain,
                                 num_groups=num_groups,
                                 routing_priority=routing_priority,
                                 stat_test_plan=stat_test_plan,
                                 statement=question)
    return prompt

def build_comparison_analysis_prompt(question,context,comparison_type,statistical_test,df_preview,descriptive_statistics,inferential_statistics):
    with open(PROMPTS_DIR / "comparison_analysis_prompt.txt") as f:
        template = f.read()  
        prompt = template.format(question=question,
                                 context=context,
                                 comparison_type=comparison_type,
                                 statistical_test=statistical_test,
                                 df_preview=df_preview,
                                 descriptive_statistics=descriptive_statistics,
                                 inferential_statistics=inferential_statistics)
    return prompt

def build_analytics_prompt(question, context, results_preview, computed_statistics_preview):
    return f"""
Your Role:
You are an analytics narration assistant providing neutral statistical summaries. 

Your Context:
You are summarizing the analysis done on the {context}

Your Task:
Act as a data analyst and use a technical and statistical tone for an audience of other data analysts.

Your Constraints:
-Use ONLY the information provided to inform your answers. 
-Do not invent statistics, trends, causes, or context.
-If the provided data is incomplete or insufficient for an evidence-based insight, say so clearly.
-Do not infer causality, forecasts, projections, or macroeconomic explanations unless explicitly present.
-Avoid causal or macroeconomic interpretation unless the computed outputs explicitly support it.
-Do not provide recommendations, actions, or next steps.
-Avoid domain interpretations unless explicitly supported by the provided context.

Answer the users question:
{question}

Use the computed outputs below.

Computed Results:
{results_preview}

Statistics:
{computed_statistics_preview}

Return the following items:
1. A concise 2-3 sentence analytical summary of the provided information. This summary should be non-speculative and grounded in the provided outputs.
2. Three evidence-based insights in bullet points. Keep them statistical and evidence-based.
3. One caution or limitation of the provided analysis.
        """
    
def build_timeframe_prompt(question,todays_date,aggregation_period):
    with open(PROMPTS_DIR / "timeframe_prompt.txt") as f:
        template = f.read()  
        prompt = template.format(todays_date=todays_date,
                                 aggregation_period=aggregation_period,
                                 question=question)
    return prompt

def timeframe_validation_failed_prompt(question,prev_date_range):
    with open(PROMPTS_DIR / "timeframe_validation_failed_prompt.txt") as f:
        template = f.read()  
        prompt = template.format(question=question,
                                 prev_date_range=prev_date_range)
    return prompt

def build_timeframe_aggregation_prompt(question):
    with open(PROMPTS_DIR / "timeframe_aggregation_prompt.txt", "r", encoding="utf-8") as f:
        template = f.read()  
        prompt = template.format(question=question)
    return prompt

def build_general_assistant_prompt(question,available_series,recent_history=None):
    with open(PROMPTS_DIR / "general_assistant_prompt.txt") as f:
        template = f.read()

        prompt = template.format(question=question,available_series=available_series,recent_history=recent_history)
    return prompt

def run_prompt(prompt,max_tokens=500):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    summary = message.content[0].text
    return summary

def run_tool_prompt(tools,message,max_tokens=500):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": message
            }
        ],
    )
    return message.content

def build_context(series_ids):
    context=""

    for series in series_ids:
        metadata=db.get_series_metadata(series_id=series)
        print(f"{metadata['title']}")
        context+=f"""This is the {metadata['title'][0]} dataset. 
        About the dataset:
        {metadata['notes'][0]}
        """
    return context

def run_comparison_analysis(question,context,comparison_type,statistical_test,df_preview,descriptive_statistics,inferential_statistics):
    return run_prompt(build_comparison_analysis_prompt(question,context,comparison_type,statistical_test,df_preview,descriptive_statistics,inferential_statistics))

def run_ranking_analysis(question,context,df,ranked_df,sort_field,ascending,n,aggregation_method,group_by):
    return run_prompt(build_ranking_analysis_prompt(question,context,df,ranked_df,sort_field,ascending,n,aggregation_method,group_by))

def run_pearson_correlation_analysis(question,context,df,ranked_df):
    return run_prompt(build_pearson_correlation_analysis_prompt(question,context,df,ranked_df))

def run_spearman_correlation_analysis(question,context,df,ranked_df,spearman_reason):
    return run_prompt(build_spearman_correlation_analysis_prompt(question,context,df,ranked_df,spearman_reason))

def run_general_assistant(question,available_series,recent_history,max_tokens=250):
    return run_prompt(build_general_assistant_prompt(question,available_series,recent_history),max_tokens)

def run_conversation_action(user_input,chat_history):
    return run_prompt(build_conversation_action_prompt(user_input,chat_history))

def run_followup(chat_history,current_user_question):
    return run_prompt(build_followup_prompt(chat_history,current_user_question))

def run_clarification_prompt(original_question,analysis_response,follow_up_question):
    return run_prompt(build_clarification_prompt(original_question,analysis_response,follow_up_question))

def run_series_intent_prompt(question):
    return run_prompt(build_series_intent_prompt(question))

def comparison_method_intent(question,date_grain,num_groups,routing_priority,stat_test_plan):
    return run_prompt(build_comparison_method_prompt(question,date_grain,num_groups,routing_priority,stat_test_plan))