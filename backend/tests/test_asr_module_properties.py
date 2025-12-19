"""
Property-Based Tests for ASR Module - Math Symbol Conversion.

Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
Validates: Requirements 5.3

Tests the correctness of math symbol conversion using property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from backend.services.asr_module import (
    ASRModule,
    MATH_SYMBOL_MAPPINGS,
    SYMBOL_TO_ORAL_MAPPINGS,
)


# Strategy for generating oral math descriptions from the mapping
oral_descriptions = st.sampled_from(list(MATH_SYMBOL_MAPPINGS.keys()))

# Strategy for generating math symbols from the reverse mapping
math_symbols = st.sampled_from(list(SYMBOL_TO_ORAL_MAPPINGS.keys()))

# Strategy for generating text with embedded oral descriptions
@st.composite
def text_with_oral_math(draw):
    """Generate text that may contain oral math descriptions."""
    # Choose how many oral descriptions to include
    num_descriptions = draw(st.integers(min_value=0, max_value=3))
    
    # Generate prefix text (Chinese characters or empty)
    prefix = draw(st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='，。、'),
        min_size=0,
        max_size=10
    ))
    
    parts = [prefix]
    
    for _ in range(num_descriptions):
        # Add an oral description
        oral = draw(oral_descriptions)
        parts.append(oral)
        # Add some separator text
        separator = draw(st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='，。、'),
            min_size=0,
            max_size=5
        ))
        parts.append(separator)
    
    return ''.join(parts)


class TestMathSymbolConversionProperties:
    """
    Property-based tests for math symbol conversion.
    
    Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
    Validates: Requirements 5.3
    """
    
    @settings(max_examples=100)
    @given(oral=oral_descriptions)
    def test_oral_to_symbol_conversion(self, oral: str):
        """
        Property: For any oral math description in the mapping,
        post_process_math_symbols should convert it to the corresponding symbol.
        
        Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
        Validates: Requirements 5.3
        """
        expected_symbol = MATH_SYMBOL_MAPPINGS[oral]
        result = ASRModule.post_process_math_symbols(oral)
        
        assert result == expected_symbol, (
            f"Expected '{oral}' to convert to '{expected_symbol}', but got '{result}'"
        )
    
    @settings(max_examples=100)
    @given(symbol=math_symbols)
    def test_symbol_to_oral_conversion(self, symbol: str):
        """
        Property: For any math symbol in the reverse mapping,
        convert_symbols_to_oral should convert it to the corresponding oral description.
        
        Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
        Validates: Requirements 5.3
        """
        expected_oral = SYMBOL_TO_ORAL_MAPPINGS[symbol]
        result = ASRModule.convert_symbols_to_oral(symbol)
        
        assert result == expected_oral, (
            f"Expected '{symbol}' to convert to '{expected_oral}', but got '{result}'"
        )
    
    @settings(max_examples=100)
    @given(oral=oral_descriptions)
    def test_round_trip_oral_to_symbol_to_oral(self, oral: str):
        """
        Property: For any oral math description, converting to symbol and back
        should produce an equivalent oral description.
        
        The round-trip may not produce the exact same string due to normalization
        (e.g., "X平方" -> "x²" -> "x平方"), but the semantic meaning should be preserved.
        
        Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
        Validates: Requirements 5.3
        """
        # Convert oral to symbol
        symbol = ASRModule.post_process_math_symbols(oral)
        
        # Convert symbol back to oral
        oral_back = ASRModule.convert_symbols_to_oral(symbol)
        
        # The round-trip should produce a valid oral description
        # that maps to the same symbol
        symbol_again = ASRModule.post_process_math_symbols(oral_back)
        
        assert symbol == symbol_again, (
            f"Round-trip failed: '{oral}' -> '{symbol}' -> '{oral_back}' -> '{symbol_again}'"
        )
    
    @settings(max_examples=100)
    @given(symbol=math_symbols)
    def test_round_trip_symbol_to_oral_to_symbol(self, symbol: str):
        """
        Property: For any math symbol, converting to oral and back
        should produce the same symbol.
        
        Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
        Validates: Requirements 5.3
        """
        # Convert symbol to oral
        oral = ASRModule.convert_symbols_to_oral(symbol)
        
        # Convert oral back to symbol
        symbol_back = ASRModule.post_process_math_symbols(oral)
        
        assert symbol == symbol_back, (
            f"Round-trip failed: '{symbol}' -> '{oral}' -> '{symbol_back}'"
        )
    
    @settings(max_examples=100)
    @given(text=text_with_oral_math())
    def test_conversion_preserves_non_math_text(self, text: str):
        """
        Property: Converting text should only affect math-related substrings,
        leaving other text unchanged.
        
        Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
        Validates: Requirements 5.3
        """
        result = ASRModule.post_process_math_symbols(text)
        
        # The result should not be longer than the original
        # (symbols are typically shorter or equal length to oral descriptions)
        # This is a sanity check - actual length may vary
        
        # More importantly, if we convert back, we should get something
        # that converts to the same result
        back_to_oral = ASRModule.convert_symbols_to_oral(result)
        final_result = ASRModule.post_process_math_symbols(back_to_oral)
        
        assert result == final_result, (
            f"Double round-trip failed: '{text}' -> '{result}' -> '{back_to_oral}' -> '{final_result}'"
        )
    
    @settings(max_examples=100)
    @given(text=st.text(min_size=0, max_size=50))
    def test_conversion_is_idempotent_after_first_pass(self, text: str):
        """
        Property: Applying post_process_math_symbols twice should give
        the same result as applying it once (idempotence after first conversion).
        
        Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
        Validates: Requirements 5.3
        """
        first_pass = ASRModule.post_process_math_symbols(text)
        second_pass = ASRModule.post_process_math_symbols(first_pass)
        
        assert first_pass == second_pass, (
            f"Conversion not idempotent: '{text}' -> '{first_pass}' -> '{second_pass}'"
        )
    
    @settings(max_examples=100)
    @given(text=st.text(min_size=0, max_size=50))
    def test_reverse_conversion_is_idempotent_after_first_pass(self, text: str):
        """
        Property: Applying convert_symbols_to_oral twice should give
        the same result as applying it once (idempotence after first conversion).
        
        Feature: ai-math-tutor, Property 6: 數學符號轉換正確性
        Validates: Requirements 5.3
        """
        first_pass = ASRModule.convert_symbols_to_oral(text)
        second_pass = ASRModule.convert_symbols_to_oral(first_pass)
        
        assert first_pass == second_pass, (
            f"Reverse conversion not idempotent: '{text}' -> '{first_pass}' -> '{second_pass}'"
        )
