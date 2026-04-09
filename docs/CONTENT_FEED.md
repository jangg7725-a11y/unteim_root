# 탐색 피드 콘텐츠 갱신

운트임 웹 **탐색** 탭의 카드·카테고리는 정적 파일로 제공됩니다.

## 파일 위치

`frontend/public/data/content_feed.json`

빌드 후에는 `dist/data/content_feed.json`으로 복사되며, 배포 시 이 경로만 갈아끼우면 **앱 재빌드 없이** 월별 내용을 바꿀 수 있습니다.

## 갱신 절차 (매달)

1. `feedVersion`을 `YYYY-MM` 형식으로 올린다.  
2. `updatedAt`에 반영일을 적는다.  
3. `categories` / `items`를 수정한다.  
4. 카드의 `theme`은 `feed.css`의 `feed-card__banner--*` 클래스와 대응한다:  
   `violet` | `rose` | `amber` | `slate` | `teal` | `pink` | `indigo`  
5. 새 테마가 필요하면 `feed.css`에 `.feed-card__banner--이름` 그라데이션을 추가한다.

## `items` 필드 요약

| 필드 | 설명 |
|------|------|
| `categoryIds` | `categories`의 `id`와 매칭. `all`은 코드에서 별도 처리(전체 표시). |
| `action.type` | `"tab"`이면 앱 내 탭으로 이동. |
| `action.target` | `input` \| `report` \| `counsel` |
| `likes` / `views` / `points` | 선택. 0이면 카드 하단에 숨길 수 있음. |

운트임 철학(엔진 근거·단정 금지)에 맞게 **설명 문구**를 작성한다. 카드는 유입용이어도 본문·모달은 과장·낚시 표현을 피한다.
