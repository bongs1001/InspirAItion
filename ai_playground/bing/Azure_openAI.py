import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, TypeVar, Generic, Tuple
from enum import Enum
from dataclasses import dataclass
import json
from abc import ABC, abstractmethod

import aiohttp
from pydantic import BaseModel, Field
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.projects.models import Tool
from openai import AzureOpenAI
from azure.ai.inference import ChatCompletionsClient
import os
import time

# 환경 변수 로드
azure_endpoint = os.getenv("AZUREAIASSISTANT_ENDPOINT")
api_key = os.getenv("AZUREAIASSISTANT_API_KEY")
api_version = os.getenv("AZUREAIASSISTANT_API_VERSION")

# 환경 변수에서 API 키 가져오기
MET_data_source = os.getenv("MET_data_source")


# Azure OpenAI 클라이언트 초기화
def initialize_azure_openai_client():
    return AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version,
    )


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("curation_log.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("curation_log.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# openAI client
client = ChatCompletionsClient(
    endpoint=azure_endpoint,
    credential=AzureKeyCredential(api_key),
)

T = TypeVar("T")


# AzureAIAssistant 클래스
class AzureAIAssistant:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        # 기존 어시스턴트 목록에서 첫 번째 어시스턴트 사용
        assistants = self.client.beta.assistants.list()
        self.assistant_id = assistants.data[0].id if assistants.data else None
        logger.info(f"사용할 어시스턴트 ID: {self.assistant_id}")

    def wait_for_run_completion(self, thread_id, run_id, max_wait_time=60):
        """
        런 완료를 기다리는 메서드
        """
        start_time = time.time()
        print("분석 중", end="", flush=True)
        while True:
            # 런 상태 확인
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run_id
            )
            # 런 상태에 따른 처리
            if run.status == "completed":
                print("\n분석 완료!")
                return True
            elif run.status in ["failed", "cancelled"]:
                print(f"\n분석 중 오류 발생: {run.status}")
                return False
            # 최대 대기 시간 초과 확인
            if time.time() - start_time > max_wait_time:
                print("\n분석 시간 초과")
                return False
            # 로딩 애니메이션
            print(".", end="", flush=True)
            time.sleep(1)

    def get_last_assistant_message(self, thread_id):
        """
        스레드의 마지막 어시스턴트 메시지 가져오기
        """
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                return msg.content[0].text.value
        return None

    def test_agent(self, artwork_name, debug=False):
        """
        에이전트 테스트 함수
        Args:
        artwork_name (str): 분석할 예술 작품명
        debug (bool): 디버그 모드 활성화 여부
        """
        try:
            # 디버그 모드일 경우에만 상세 로깅
            if debug:
                logging.getLogger().setLevel(logging.INFO)
            # 스레드 생성
            thread = self.client.beta.threads.create()
            # 메시지 생성
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Provide a comprehensive analysis of the artwork '{artwork_name}'",
            )
            # 스레드 런 생성
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=self.assistant_id
            )
            # 런 완료 대기
            if self.wait_for_run_completion(thread.id, run.id):
                # 마지막 어시스턴트 메시지 가져오기
                analysis = self.get_last_assistant_message(thread.id)
                return {"artwork": artwork_name, "analysis": analysis}
            return None
        except Exception as e:
            # 디버그 모드일 경우에만 전체 오류 출력
            if debug:
                print(f"에이전트 테스트 중 오류 발생: {e}")
            return None


# AzureAIAssistant 클래스
class Assistant:
    async def call_action(self, task):
        # 작업을 처리하는 로직 (여기서는 단순히 출력 예시로)
        print(f"Processing task: {task}")
        # 여기서 문자열을 반환하고 있습니다. dictionary를 반환하도록 수정해야 합니다.
        return Result(success=True, data={"task": task, "objectIDs": []})


# 향상된 Result 타입
@dataclass
class Result(Generic[T]):
    """API 결과를 담는 일반화된 컨테이너"""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None


# 큐레이션 스타일 정의
class CurationStyle(Enum):
    EMOTIONAL = "Emotional"
    INTERPRETIVE = "Interpretive"
    HISTORICAL = "Historical"
    CRITICAL = "Critical"
    NARRATIVE = "Narrative"
    CONTEMPORARY_ART_CRITIC = "Contemporary_Art_Critic"
    ART_APPRAISER = "Art_Appraiser"
    AESTHETIC_EVALUATION = "Aesthetic_Evaluation"
    IMAGE_INTERPRETER = "Image_Interpreter"
    EDUCATIONAL = "Educational"


# 기본 API 클라이언트 추상 클래스
class BaseAPIClient(ABC):
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self.session = session
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=30)

    @abstractmethod
    async def handle_response(self, response: aiohttp.ClientResponse) -> Result:
        pass

    async def make_request(self, method: str, endpoint: str, **kwargs) -> Result:
        try:
            async with self.session.request(
                method, f"{self.base_url}/{endpoint}", timeout=self.timeout, **kwargs
            ) as response:
                return await self.handle_response(response)
        except asyncio.TimeoutError:
            return Result(success=False, error="Request timeout")
        except Exception as e:
            return Result(success=False, error=str(e))


# 향상된 데이터 모델
@dataclass
class ImageAnalysis:
    dense_caption: str
    tags: List[str]
    confidence_score: float

    def to_dict(self) -> Dict:
        return {
            "dense_caption": self.dense_caption,
            "tags": self.tags,
            "confidence_score": self.confidence_score,
        }


@dataclass
class ArtReference:
    title: str
    artist: str
    period: str
    medium: str
    description: str
    url: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "period": self.period,
            "medium": self.medium,
            "description": self.description,
            "url": self.url,
        }


@dataclass
class CurationRequest:
    user_prompt: str
    selected_style: CurationStyle
    image_analysis: ImageAnalysis
    reference_search: Optional[str] = None
    language: str = "ko"  # 언어 설정

    def to_dict(self) -> Dict:
        return {
            "user_prompt": self.user_prompt,
            "selected_style": self.selected_style.value,
            "image_analysis": self.image_analysis.to_dict(),
            "reference_search": self.reference_search,
            "language": self.language,
        }


@dataclass
class CurationResult:
    style: CurationStyle
    content: str
    references: List[ArtReference]
    metadata: Dict
    language: str = "ko"  # 언어 설정

    def to_dict(self) -> Dict:
        return {
            "style": self.style.value,
            "content": self.content,
            "references": [ref.to_dict() for ref in self.references],
            "metadata": self.metadata,
            "language": self.language,
        }


# 향상된 Met Museum API 클라이언트
class MetMuseumClient(BaseAPIClient):
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session, MET_data_source)

    async def handle_response(self, response: aiohttp.ClientResponse) -> Result:
        if response.status == 200:
            data = await response.json()
            return Result(success=True, data=data)
        return Result(success=False, error=f"API error: {response.status}")

    async def search_artworks(self, query: str, has_images: bool = True) -> Result:
        return await self.make_request(
            "GET", "search", params={"q": query, "hasImages": has_images}
        )

    async def get_artwork_details(self, object_id: int) -> Result:
        return await self.make_request("GET", f"objects/{object_id}")


# 향상된 큐레이션 서비스
class EnhancedCurationService:
    def __init__(
        self,
        met_client: MetMuseumClient,
        gpt_client: Any,
        session: aiohttp.ClientSession,
    ):
        self.met_client = met_client
        self.gpt_client = gpt_client
        self.session = session
        self._init_style_prompts()
        self.assistant = Assistant()

    def _init_style_prompts(self):
        """스타일별 프롬프트 템플릿 로드와 참조 데이터 요구사항 정의"""
        self.style_prompts = {
            CurationStyle.EMOTIONAL: {
                "prompt": """감성적이고 서정적인 관점에서 작품을 분석하여 다음 요소들을 포함해 서술해주세요:
                    - 작품이 전달하는 주요 감정과 분위기
                    - 시각적 요소가 불러일으키는 감정적 반응
                    - 작품 속 순간이 주는 특별한 정서
                    - 관객이 느낄 수 있는 공감과 울림
                    - 작품의 서정적 특징과 시적 표현""",
                "required_references": ["similar_emotional_works", "artist_background"],
            },
            CurationStyle.INTERPRETIVE: {
                "prompt": """작품의 의미와 예술적 기법을 심층적으로 분석하여 다음 요소들을 포함해 서술해주세요:
                    - 작품의 주요 시각적 요소와 상징성
                    - 구도와 색감의 효과
                    - 작가의 의도와 메시지
                    - 사용된 예술적 기법과 그 효과
                    - 작품이 전달하는 철학적/개념적 의미""",
                "required_references": ["artistic_techniques", "symbolism_history"],
            },
            CurationStyle.HISTORICAL: {
                "prompt": """작품을 역사적, 미술사적 맥락에서 심도 있게 분석하여 다음 요소들을 포함해 서술해주세요:
                    - 작품이 제작된 시대적 배경과 특징
                    - 유사한 예술 경향이나 작품들과의 관계
                    - 현대 미술사에서의 위치와 의의
                    - 작품의 예술적/사회적 영향력
                    - 역사적 맥락에서의 작품 해석""",
                "required_references": ["historical_context", "art_movement_history"],
            },
            CurationStyle.CRITICAL: {
                "prompt": """전문적이고 균형 잡힌 시각으로 작품을 비평하여 다음 요소들을 포함해 서술해주세요:
                    - 작품의 기술적 완성도와 예술성
                    - 창의성과 혁신성 분석
                    - 강점과 개선 가능성
                    - 예술적 성취와 한계점
                    - 작품의 독창성과 차별성""",
                "required_references": ["contemporary_critiques", "technical_analysis"],
            },
            CurationStyle.NARRATIVE: {
                "prompt": """작품을 매력적인 이야기로 풀어내어 다음 요소들을 포함해 서술해주세요:
                    - 작품 속 장면의 생생한 묘사
                    - 등장 요소들 간의 관계와 이야기
                    - 작품 속 시간의 흐름과 변화
                    - 장면 속에 숨겨진 드라마와 서사
                    - 관객이 상상할 수 있는 전후 맥락""",
                "required_references": ["narrative_context", "literary_connections"],
            },
            CurationStyle.CONTEMPORARY_ART_CRITIC: {
                "prompt": """현대 예술 트렌드의 관점에서 작품을 분석하여 다음 요소들을 포함해 서술해주세요:
                    - 현대 예술 동향과의 연관성
                    - 디지털/기술적 혁신 요소
                    - 현대 사회/문화적 맥락에서의 의미
                    - 최신 예술 트렌드와의 접점
                    - 미래 예술 발전에 대한 시사점""",
                "required_references": ["contemporary_trends", "digital_art_context"],
            },
            CurationStyle.ART_APPRAISER: {
                "prompt": """현대 예술 트렌드의 관점에서 작품을 분석하여 다음 요소들을 포함해 서술해주세요:
                    - 현대 예술 동향과의 연관성
                    - 디지털/기술적 혁신 요소
                    - 현대 사회/문화적 맥락에서의 의미
                    - 최신 예술 트렌드와의 접점
                    - 미래 예술 발전에 대한 시사점""",
                "required_references": ["contemporary_trends", "digital_art_context"],
            },
            CurationStyle.AESTHETIC_EVALUATION: {
                "prompt": """현대 미술에 대한 깊은 애정과 이해를 가진 열정적인 미술 옹호자로서, 다음 요소들을 고려하여 작품을 긍정적이고 영감을 주는 방식으로 분석해주세요:
                    - 작품의 혁신적 측면과 독창성
                    - 뛰어난 색채와 구도의 활용
                    - 작가의 비전과 그 탁월한 표현
                    - 관객에게 미치는 감정적, 지적 영향
                    - 현대 미술사적 맥락에서의 중요성
                    작품의 장점을 강조하고 예술적 가치를 생생하게 설명해주세요.""",
                "required_references": ["contemporary_trends", "digital_art_context"],
            },
            CurationStyle.IMAGE_INTERPRETER: {
                "prompt": """시각장애인을 위한 이미지 설명 전문가로서, 다음 요소들을 포함하여 명확하고 상세한 설명을 제공해주세요:
                    - 이미지의 전체적인 구성과 주요 요소
                    - 색상, 형태, 질감의 상세한 묘사
                    - 요소들 간의 공간적 관계와 배치
                    - 이미지가 전달하는 분위기나 감정
                    - 중요한 세부사항이나 특징적인 요소
                    촉각적 또는 청각적 경험과 연관지어 설명해주세요.""",
                "required_references": ["contemporary_trends", "digital_art_context"],
            },
            CurationStyle.EDUCATIONAL: {
                "prompt": """교육적 관점에서 작품을 분석하여 다음 요소들을 포함해 서술해주세요:
                    - 작품의 긍정적 측면과 성취된 학습 목표
                        * 기술적 완성도와 성공적인 표현 요소
                        * 효과적으로 전달된 메시지나 의도
                        * 창의적 시도와 혁신적 접근
                    - 발전 가능한 영역과 학습 제안
                        * 더 발전시킬 수 있는 기술적 요소
                        * 보완하면 좋을 표현적 측면
                        * 시도해볼 수 있는 새로운 접근방식
                    - 구체적인 학습 목표와 실천 방안
                        * 단기적으로 향상시킬 수 있는 부분
                        * 장기적인 발전을 위한 학습 방향
                        * 참고할 만한 작품이나 기법 추천
                    긍정적인 피드백을 중심으로, 발전 가능성을 구체적으로 제시해주세요.""",
                "required_references": ["contemporary_trends", "digital_art_context"],
            },
        }

    async def generate_curation(
        self, request: CurationRequest
    ) -> Result[CurationResult]:
        try:
            # 병렬로 참조 작품과 컨텍스트 데이터 수집
            ref_artworks_task = self._search_reference_artworks(request)
            context_data_task = self._search_additional_context(request)

            ref_artworks, context_data = await asyncio.gather(
                ref_artworks_task, context_data_task
            )

            if not ref_artworks.success:
                return Result(success=False, error=ref_artworks.error)

            # 데이터 통합 및 큐레이션 생성
            integrated_data = self._integrate_data(
                request, ref_artworks.data, context_data.data
            )
            curation_text = await self._generate_gpt_curation(integrated_data)

            if not curation_text.success:
                return Result(success=False, error=curation_text.error)

            # 결과 포맷팅
            result = self._format_results(
                curation_text.data, ref_artworks.data, request
            )
            return Result(success=True, data=result)
        except Exception as e:
            return Result(success=False, error=str(e))

    async def _search_reference_artworks(
        self, request: CurationRequest
    ) -> Result[List[Dict]]:
        """참조 작품 검색 - 비동기 처리"""
        try:
            style_refs = self.style_prompts[request.selected_style][
                "required_references"
            ]
            search_tasks = []
            for ref_type in style_refs:
                search_query = (
                    f"{request.reference_search} {ref_type.replace('_', ' ')}"
                )
                search_tasks.append(self.assistant.call_action(search_query))

            search_results = await asyncio.gather(*search_tasks)
            processed_results = []
            for result in search_results:
                if result.success and result.data.get("objectIDs"):
                    artwork_tasks = [
                        self.assistant.call_action(f"get_artwork_details_{object_id}")
                        for object_id in result.data["objectIDs"][:3]
                    ]
                    artwork_details = await asyncio.gather(*artwork_tasks)
                    processed_results.extend(
                        [detail.data for detail in artwork_details if detail.success]
                    )
                # Assistant.call_action이 문자열을 반환하는 경우 처리
                elif result.success and isinstance(result.data, str):
                    # 문자열 결과를 처리하는 로직 추가
                    processed_results.append({"description": result.data})
            return Result(success=True, data=processed_results)
        except Exception as e:
            return Result(success=False, error=str(e))

    async def _search_additional_context(
        self, request: CurationRequest
    ) -> Result[Dict]:
        """추가 컨텍스트 정보 검색 - 비동기 처리"""
        try:
            context_data = {}
            style_context = self.style_prompts[request.selected_style][
                "required_references"
            ]

            async def fetch_context(context_type: str) -> Tuple[str, Any]:
                search_query = f"{request.reference_search} {context_type.replace('_', ' ')} art history"
                result = await self.assistant.call_action(search_query)
                return context_type, result

            # 병렬로 컨텍스트 데이터 수집
            context_tasks = [
                fetch_context(context_type) for context_type in style_context
            ]
            results = await asyncio.gather(*context_tasks)
            context_data = dict(results)

            # reference_search가 없는 경우 Bing 검색을 통해 추가 컨텍스트 정보 가져오기
            if not request.reference_search:
                additional_context_tasks = []
                for context_type in style_context:
                    search_query = f"{context_type.replace('_', ' ')} art history"
                    additional_context_tasks.append(
                        self.assistant.call_action(search_query, limit=10)
                    )  # 결과 제한

                additional_results = await asyncio.gather(*additional_context_tasks)
                for result in additional_results:
                    if result.success and isinstance(result.data, str):
                        context_data[context_type] = result.data

            return Result(success=True, data=context_data)

        except Exception as e:
            return Result(success=False, error=str(e))

    def _integrate_data(
        self, request: CurationRequest, ref_artworks: List[Dict], context_data: Dict
    ) -> Dict:
        """데이터 통합"""
        return {
            "request": request.to_dict(),
            "reference_artworks": ref_artworks,
            "context_data": context_data,
        }

    async def _generate_gpt_curation(self, integrated_data: Dict) -> Result[str]:
        """GPT를 사용한 큐레이션 텍스트 생성"""
        try:
            prompt = self._create_gpt_prompt(integrated_data)
            response = await self._generate_assistant_response(prompt)
            return Result(success=True, data=response)
        except Exception as e:
            return Result(success=False, error=str(e))

    def _create_gpt_prompt(self, integrated_data: Dict) -> str:
        """GPT 프롬프트 생성"""
        request = integrated_data["request"]
        style_prompt = self.style_prompts[CurationStyle(request["selected_style"])][
            "prompt"
        ]
        reference_artworks = integrated_data["reference_artworks"]
        context_data = integrated_data["context_data"]

        # 프롬프트 생성 로직
        prompt = f"{style_prompt}\n\n"
        prompt += "참조 작품:\n"
        for artwork in reference_artworks:
            prompt += f"- {artwork['title']} by {artwork['artist']}\n"
        prompt += "\n추가 컨텍스트:\n"
        for key, value in context_data.items():
            prompt += f"- {key}: {value}\n"
        return prompt

    async def _generate_assistant_response(self, prompt: str) -> str:
        """어시스턴트 응답 생성"""
        try:
            # 스레드 생성
            thread = self.gpt_client.client.beta.threads.create()
            logger.info(f"새 스레드 생성: {thread.id}")
            # 메시지 생성
            message = self.gpt_client.client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=prompt
            )
            logger.info(f"스레드 메시지 생성: {message.id}")
            # 스레드 런 생성
            run = self.gpt_client.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=self.gpt_client.assistant_id
            )
            logger.info(f"스레드 런 생성: {run.id}")
            # 런 완료 대기
            if self.gpt_client.wait_for_run_completion(thread.id, run.id):
                # 마지막 어시스턴트 메시지 가져오기
                response = self.gpt_client.get_last_assistant_message(thread.id)
                return response
            return None
        except Exception as e:
            logger.error(f"어시스턴트 응답 생성 중 오류 발생: {e}")
            return None

    def _format_results(
        self, curation_text: str, references: List[Dict], request: CurationRequest
    ) -> CurationResult:
        """결과 포맷팅"""
        art_references = [ArtReference(**ref) for ref in references]
        return CurationResult(
            style=request.selected_style,
            content=curation_text,
            references=art_references,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "style": request.selected_style.value,
                "reference_count": len(references),
            },
        )

    async def _fetch_context_data(self, search_query: str) -> Any:
        """컨텍스트 데이터를 가져오는 메서드"""
        try:
            async with self.session.get(
                f"{MET_data_source}/search?q={search_query}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return None
        except Exception as e:
            return None


class AsyncCurationClient:
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.met_client = MetMuseumClient(self.session)
        self.gpt_client = AzureAIAssistant()
        self.curation_service = EnhancedCurationService(
            met_client=self.met_client, gpt_client=self.gpt_client, session=self.session
        )
        return self.curation_service

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()


#################################################################################
# main 함수
async def main():
    async with AsyncCurationClient() as curation_service:
        request = CurationRequest(
            # user_prompt="피카소 스타일 화려한 색채와 동적인 구성으로 서울 도시풍경 그리기 감성적인 스타일",
            user_prompt="in the style of Vincent van Gogh's Starry Night, oil painting",
            selected_style=CurationStyle.CRITICAL,
            image_analysis=ImageAnalysis(
                # dense_caption="painting of a Seoul cityscape in the style of Picasso, with abstract forms, vibrant colors, and dynamic composition",
                # tags=["art", "painting", "Picasso"],
                dense_caption="oil painting of a night street with a cafe in the style of John Singer Sargent, with lights, people walking around, bright moonlight, low angle, expressive brushstrokes, detailed background to add depth --ar 63:128 --stylize 750 --v 6.1",
                tags=["art", "painting"],
                confidence_score=0.95,
            ),
            reference_search="Critical",
            language="ko",  # 언어 설정
        )

        result = await curation_service.generate_curation(request)

        if result.success:
            original_text = str(result.data.to_dict())  # 결과를 문자열로 변환
            sentences = original_text.split(". ")  # 문장 단위로 줄바꿈 출력
            for sentence in sentences:
                print(sentence.strip())

        else:
            print(f"Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
