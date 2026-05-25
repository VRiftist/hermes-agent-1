# Token Budget Per Model

*52.4s*

The realistic 12K token budget per model refers to the maximum number of tokens a model can process in a single interaction, often constrained by the model's context length. For Qwen3 variants, this budget is model-specific, determined by their architecture and optimization. For example, qwen3:8b (8 billion parameters) and qwen3:14b (14 billion parameters) likely support a 12K context window, while qwen3-coder:30b (30 billion parameters) may offer extended context lengths (e.g., 100K tokens) due to larger scale and optimized memory management. However, practical budgets may vary based on use cases, such as inference speed or resource constraints.  

**Identity Overhead vs. Working Context**  
Identity overhead refers to the tokens required for model-specific operations, such as internal state maintenance, system prompts, or metadata. For instance, a model might allocate ~1-2K tokens for identity overhead (e.g., system messages, role definitions), leaving ~11K tokens for working context (user input/output). This ratio depends on the model's design: smaller models (e.g., 8b) may have higher overhead due to less efficient resource allocation, while larger models (e.g., 30b) can optimize overhead to prioritize working context.  

**Model-Specific Budgets**  
Yes, the token budget should be model-specific. Larger models (like qwen3-coder:30b) can handle more tokens due to advanced techniques like memory-efficient attention mechanisms or sparse activation. However, even within the same series, smaller models (e.g., 8b vs. 14b) may have stricter budgets due to resource limits. For example, qwen3:8b might prioritize a 12K budget for balance between performance and cost, while qwen3-coder:30b could scale to 100K tokens, enabling complex tasks like code generation over long contexts.  

**Key Considerations**  
1. **Scalability**: Larger models can process more tokens, but practical budgets depend on hardware and use cases. For example, a 30b model might support 100K tokens but require higher computational resources.  
2. **Efficiency**: Identity overhead is critical for tasks like code generation (qwen3-coder) or multilingual support, where system prompts or metadata dominate token usage.  
3. **Trade-offs**: A 12K budget is practical for most applications, but specialized models (e.g., coders) may need longer contexts for complex workflows.  

In summary, the 12K token budget is a practical limit for many models, but it is model-specific and influenced
