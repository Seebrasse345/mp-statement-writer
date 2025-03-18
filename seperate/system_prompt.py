"""
This module contains the system prompt templates and tone instructions for the MP Statement Rewriter.
You can edit the prompt templates in this file to customize the AI's behavior.
"""

# System prompt for the LLM
SYSTEM_PROMPT = "You are a skilled political communication specialist who helps transform official government statements into personalized MP communications."

# System prompt for refresh/regeneration
REFRESH_SYSTEM_PROMPT = "You are a skilled political communication specialist who excels at creative reframing and finding fresh approaches to political messaging."

# Dictionary of tone instructions for different communication styles
TONE_INSTRUCTIONS = {
    "Neutral/Balanced": """
Strike a moderate, even-handed tone that acknowledges different perspectives. 
- Use measured language that avoids strong emotional appeals
- Present information in a fair and objective manner
- Acknowledge complexity without taking strong positions
- Use balanced phrasing like "on one hand... on the other hand"
- Convey thoughtfulness and consideration of multiple viewpoints
""",
    "Empathetic/Caring": """
Express genuine concern and understanding for constituents' feelings and experiences.
- Use warm, compassionate language that validates emotions
- Acknowledge difficulties people may be experiencing
- Include phrases like "I understand that..." or "I know many of you are feeling..."
- Demonstrate that you're listening and that constituent concerns matter
- Balance empathy with hope and solutions
""",
    "Authoritative/Confident": """
Project strength, expertise and decisiveness.
- Use clear, direct statements without hedging language
- Emphasize concrete actions and solutions
- Include phrases that demonstrate leadership and conviction
- Maintain a formal, professional tone
- Reference expertise, experience, or past achievements where relevant
""",
    "Optimistic/Positive": """
Focus on opportunities, solutions and positive outcomes.
- Emphasize progress, improvements, and future benefits
- Use uplifting language and hopeful framing
- Highlight what's working well and potential for positive change
- Include forward-looking statements and vision
- Balance optimism with realism to maintain credibility
""",
    "Concerned/Serious": """
Convey appropriate gravity for serious issues while maintaining constructive engagement.
- Use language that acknowledges the seriousness of challenges
- Express appropriate concern without alarming unnecessarily
- Demonstrate that you're taking the issue seriously
- Balance concern with determination to address problems
- Avoid minimizing genuine problems
""",
    "Conversational/Friendly": """
Adopt an approachable, personal tone as if speaking directly to constituents.
- Use relaxed, everyday language rather than formal political speech
- Include occasional contractions and more casual phrasing
- Write as if having a one-to-one conversation
- Create a sense of personal connection and accessibility
- Maintain professionalism while being personable
""",
    "Formal/Professional": """
Maintain a dignified, traditional political communication style.
- Use more formal language and structured sentences
- Maintain appropriate distance and decorum
- Avoid colloquialisms and overly casual expressions
- Project statesmanship and institutional respect
- Focus on precision of language and clarity of message
""",
    "Urgent/Call to Action": """
Convey immediacy and encourage specific responses or engagement.
- Use language that emphasizes timeliness and importance
- Include clear calls to action where appropriate
- Create a sense of momentum and necessary response
- Use slightly more dynamic and energetic language
- Balance urgency with reassurance to avoid causing anxiety
"""
}

# Default tone instruction if none specified
DEFAULT_TONE_INSTRUCTION = "Use a natural, conversational tone that feels personal and authentic."


def construct_prompt(raw_text, context, audience, tone, accepted_responses, rejected_responses=None):
    """Construct a prompt for the LLM that includes all necessary context"""
    # Get tone instructions
    tone_instructions = TONE_INSTRUCTIONS.get(tone, DEFAULT_TONE_INSTRUCTION)
    
    # Format accepted examples
    accepted_examples = ""
    if accepted_responses:
        accepted_examples = "## EXAMPLES TO EMULATE (these showcase the MP's voice and style):\n\n"
        for i, (response, topic, resp_tone) in enumerate(accepted_responses, 1):
            accepted_examples += f"### Example {i} "
            if resp_tone and resp_tone != "None":
                accepted_examples += f"(Tone: {resp_tone})"
            accepted_examples += f":\n\"{response}\"\n\n"
    
    # Format rejected examples
    rejected_examples = ""
    if rejected_responses and len(rejected_responses) > 0:
        rejected_examples = "## EXAMPLES TO AVOID (these were rejected or don't reflect the MP's voice well):\n\n"
        for i, (response, topic, resp_tone) in enumerate(rejected_responses, 1):
            rejected_examples += f"### Bad Example {i}:\n\"{response}\"\n\n"
            rejected_examples += f"Problem: This example doesn't fully capture the MP's voice, uses generic language, or lacks personal connection.\n\n"
    
    # Create the complete prompt
    prompt = f"""# MP STATEMENT REWRITING TASK

## OBJECTIVE:
Transform the government statement below into a personalized communication from the MP that feels authentic, locally relevant, and engaging to the specified audience. The rewritten statement should sound like it comes directly from the MP, incorporating their voice and style while addressing the specific context and audience needs.

## RAW GOVERNMENT STATEMENT: {raw_text} 

## LOCAL CONTEXT:
{context}

## TARGET AUDIENCE:
{audience}

## REQUIRED TONE: {tone}
{tone_instructions}

{accepted_examples}

{rejected_examples}

## TRANSFORMATION GUIDELINES:

1. **Authentic Voice**: 
   - Use first-person perspective ("I", "my", "our constituency")
   - Maintain the MP's conversational style shown in the examples
   - Avoid bureaucratic language and generic political phrases

2. **Local Relevance**:
   - Incorporate specific local context provided
   - Reference constituency concerns where appropriate
   - Make national announcements feel relevant to local constituents

3. **Audience Awareness**:
   - Tailor vocabulary and examples to resonate with the target audience
   - Address specific concerns this audience might have
   - Use appropriate level of detail and explanation

4. **Personal Connection**:
   - Include the MP's personal commitment to the issue
   - Reference relevant past work on similar issues when appropriate
   - Show understanding of constituent needs

5. **Clear Communication**:
   - Maintain clarity on key facts and figures from the original statement
   - Structure with clear paragraphs and logical flow
   - Avoid overly complex sentences or jargon

## OUTPUT REQUIREMENTS:
- Produce a complete, polished statement ready for publication
- Length should be appropriate to the complexity of the topic (typically 150-300 words)
- Balance faithfulness to the original information with personalization
- Do not include any explanatory notes, only provide the rewritten statement

## REWRITTEN STATEMENT:
"""
    return prompt


def construct_refresh_prompt(raw_text, context, audience, tone, accepted_examples, rejected_examples):
    """Construct a prompt for refreshing with emphasis on diversity"""
    # Get tone instructions
    tone_instructions = TONE_INSTRUCTIONS.get(tone, DEFAULT_TONE_INSTRUCTION)
    
    # Format accepted examples
    accepted_content = ""
    if accepted_examples:
        accepted_content = "## EXAMPLES TO EMULATE (these showcase the MP's voice and style):\n\n"
        for i, (response, topic, resp_tone) in enumerate(accepted_examples, 1):
            accepted_content += f"### Example {i} "
            if resp_tone and resp_tone != "None":
                accepted_content += f"(Tone: {resp_tone})"
            accepted_content += f":\n\"{response}\"\n\n"
    
    # Format rejected examples
    rejected_content = ""
    if rejected_examples and len(rejected_examples) > 0:
        rejected_content = "## EXAMPLES TO AVOID (especially the first one which was your previous attempt):\n\n"
        for i, (response, topic, resp_tone) in enumerate(rejected_examples, 1):
            label = "Your Previous Attempt" if i == 1 else f"Bad Example {i}"
            rejected_content += f"### {label}:\n\"{response}\"\n\n"
            
            if i == 1:
                rejected_content += "Problems with this version:\n"
                rejected_content += "- It didn't fully capture the MP's personal voice\n"
                rejected_content += "- The local context wasn't sufficiently incorporated\n"
                rejected_content += "- It may have used generic political language\n"
                rejected_content += "- The tone wasn't quite right for the audience\n\n"
            else:
                rejected_content += "Problem: This example doesn't effectively represent the MP's voice or connect with constituents.\n\n"
    
    # Create the complete prompt with emphasis on diversity
    prompt = f"""# MP STATEMENT REWRITING TASK (SECOND ATTEMPT)

## OBJECTIVE:
Transform the government statement below into a personalized communication from the MP. Your previous attempt was not approved, so this version needs to take a SIGNIFICANTLY DIFFERENT APPROACH while still maintaining the MP's authentic voice.

## RAW GOVERNMENT STATEMENT: {raw_text} 

## LOCAL CONTEXT:
{context}

## TARGET AUDIENCE:
{audience}

## REQUIRED TONE: {tone}
{tone_instructions}

{accepted_content}

{rejected_content}

## TRANSFORMATION REQUIREMENTS:

1. **TAKE A COMPLETELY DIFFERENT APPROACH** from your previous attempt:
   - Use a different structure and opening
   - Emphasize different aspects of the information
   - Find a fresh angle or framing for the message
   - Avoid repeating phrases, examples, or analogies from the rejected version

2. **Stronger Local Connection**:
   - More explicitly incorporate the local context provided
   - Make stronger connections to constituency-specific issues
   - Add more geographical or community-specific references
   - Show how national policies directly impact this specific constituency

3. **More Authentic Voice**:
   - Use more natural, conversational language
   - Include more personal commitment ("I am committed to..." "I've been working on...")
   - Avoid political clichés and generic phrases
   - Make it sound like a real person speaking, not a press release

4. **Better Audience Targeting**:
   - Address the specific needs and concerns of this audience more directly
   - Use language, examples, and references that will resonate with them
   - Adjust complexity and detail level to match audience expectations
   - Include specific benefits or impacts relevant to this audience

5. **More Compelling Structure**:
   - Create a stronger opening that immediately engages
   - Ensure a logical flow with clear transitions
   - Include a more memorable conclusion with clear next steps
   - Break up dense information into more digestible parts

## OUTPUT REQUIREMENTS:
- Produce a complete, polished statement ready for publication
- Length should be appropriate to the complexity of the topic (typically 150-300 words)
- Ensure this version is distinctly different from your previous attempt
- Do not include any explanatory notes, only provide the rewritten statement

## REWRITTEN STATEMENT:"""
    return prompt