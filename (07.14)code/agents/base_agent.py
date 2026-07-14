"""
agents/base_agent.py

Gemini / OpenAI 공통 LLM 호출 래퍼.
환경변수 LLM_PROVIDER 로 제공자를 선택합니다.
  - "gemini" → google-generativeai SDK (GEMINI_API_KEY)
  - "openai"  → openai SDK (OPENAI_API_KEY)

사용법:
    agent = BaseAgent()
    response = agent.generate(system_prompt="...", user_message="...")
"""

import os
from dotenv import load_dotenv

load_dotenv()


class BaseAgent:
    """LLM 제공자 분기 래퍼 클래스."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()

        if self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ValueError(
                f"지원하지 않는 LLM_PROVIDER: '{self.provider}'. "
                "'gemini' 또는 'openai'를 입력하세요."
            )

    # ──────────────────────────────────────────────────────────────
    # 초기화
    # ──────────────────────────────────────────────────────────────

    def _init_gemini(self):
        """Gemini SDK 초기화."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai 패키지가 설치되지 않았습니다. "
                "pip install google-generativeai 를 실행하세요."
            )
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._gemini_model = genai.GenerativeModel(model_name)
        print(f"[BaseAgent] Gemini 초기화 완료 — 모델: {model_name}")

    def _init_openai(self):
        """OpenAI SDK 초기화."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai 패키지가 설치되지 않았습니다. "
                "pip install openai 를 실행하세요."
            )
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        self._openai_client = __import__("openai").OpenAI(api_key=api_key)
        self._openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        print(f"[BaseAgent] OpenAI 초기화 완료 — 모델: {self._openai_model}")

    # ──────────────────────────────────────────────────────────────
    # 공통 인터페이스
    # ──────────────────────────────────────────────────────────────

    def generate(self, system_prompt: str, user_message: str) -> str:
        """
        LLM에 메시지를 보내고 응답 텍스트를 반환합니다.

        Args:
            system_prompt: 에이전트 역할 및 지침을 담은 시스템 프롬프트
            user_message:  실제 분석 요청 및 데이터가 담긴 사용자 메시지

        Returns:
            LLM이 생성한 텍스트 응답
        """
        if self.provider == "gemini":
            return self._generate_gemini(system_prompt, user_message)
        else:
            return self._generate_openai(system_prompt, user_message)

    # ──────────────────────────────────────────────────────────────
    # 내부 구현
    # ──────────────────────────────────────────────────────────────

    def _generate_gemini(self, system_prompt: str, user_message: str) -> str:
        """Gemini API 호출."""
        import google.generativeai as genai

        full_prompt = f"{system_prompt}\n\n{user_message}"
        response = self._gemini_model.generate_content(full_prompt)
        return response.text

    def _generate_openai(self, system_prompt: str, user_message: str) -> str:
        """OpenAI API 호출."""
        response = self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
