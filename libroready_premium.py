#!/usr/bin/env python3
"""
LibroReady Premium Features
- Keyword research and optimization
- BISAC category recommendations
- Book description optimizer
- Cover generator
- Print cover PDF with spine calculation
"""

import re
from collections import Counter
from docx import Document
from PIL import Image, ImageDraw, ImageFont
import io


class KeywordResearcher:
    """AI-powered keyword research for KDP"""

    # Common genres and their related keywords
    GENRE_KEYWORDS = {
        'romance': ['love', 'relationship', 'passion', 'heart', 'romance', 'lovers', 'dating', 'marriage'],
        'thriller': ['suspense', 'mystery', 'crime', 'detective', 'murder', 'investigation', 'thriller'],
        'fantasy': ['magic', 'dragon', 'quest', 'kingdom', 'sword', 'fantasy', 'adventure', 'wizard'],
        'self-help': ['guide', 'improve', 'success', 'mindset', 'growth', 'habits', 'productivity', 'life'],
        'business': ['entrepreneur', 'startup', 'business', 'marketing', 'sales', 'leadership', 'strategy'],
        'horror': ['fear', 'terror', 'haunted', 'ghost', 'supernatural', 'dark', 'nightmare'],
        'literary': ['life', 'family', 'story', 'journey', 'memoir', 'coming-of-age', 'character'],
    }

    # KDP-specific keyword patterns that work well
    KEYWORD_TEMPLATES = [
        '{genre} {format}',  # e.g., "romance novel"
        '{theme} {genre}',   # e.g., "love story"
        '{audience} {genre}',  # e.g., "young adult fantasy"
    ]

    def __init__(self, doc_path, book_title, book_description=""):
        self.doc = Document(doc_path)
        self.title = book_title
        self.description = book_description
        self.text_content = self._extract_text()

    def _extract_text(self, sample_size=5000):
        """Extract sample text from document"""
        text = []
        for para in self.doc.paragraphs[:100]:  # First 100 paragraphs
            text.append(para.text)
        full_text = ' '.join(text)
        return full_text[:sample_size]

    def analyze(self):
        """Analyze book and generate keyword recommendations"""
        # Detect genre
        detected_genre = self._detect_genre()

        # Extract key themes
        themes = self._extract_themes()

        # Generate keyword suggestions
        keywords = self._generate_keywords(detected_genre, themes)

        return {
            'genre': detected_genre,
            'themes': themes[:10],
            'suggested_keywords': keywords[:15],  # Give more options
            'recommended_7': keywords[:7],  # Top 7 for KDP
            'keyword_tips': self._get_keyword_tips(detected_genre)
        }

    def _detect_genre(self):
        """Detect book genre from content"""
        text_lower = self.text_content.lower()
        title_lower = self.title.lower()
        combined = text_lower + ' ' + title_lower

        genre_scores = {}
        for genre, keywords in self.GENRE_KEYWORDS.items():
            score = sum(combined.count(keyword) for keyword in keywords)
            genre_scores[genre] = score

        detected = max(genre_scores, key=genre_scores.get)
        return detected if genre_scores[detected] > 0 else 'literary'

    def _extract_themes(self):
        """Extract main themes/topics from book"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
                     'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which'}

        # Extract words
        words = re.findall(r'\b[a-z]{4,}\b', self.text_content.lower())

        # Filter and count
        filtered_words = [w for w in words if w not in stop_words]
        word_counts = Counter(filtered_words)

        # Get top themes
        return [word for word, count in word_counts.most_common(30)]

    def _generate_keywords(self, genre, themes):
        """Generate keyword combinations"""
        keywords = []

        # Add genre-specific keywords
        if genre in self.GENRE_KEYWORDS:
            keywords.extend(self.GENRE_KEYWORDS[genre][:3])

        # Add theme-based keywords
        keywords.extend(themes[:4])

        # Generate two-word combinations
        genre_words = self.GENRE_KEYWORDS.get(genre, [])
        for theme in themes[:5]:
            for genre_word in genre_words[:3]:
                combo = f"{theme} {genre_word}"
                if combo not in keywords:
                    keywords.append(combo)

        # Add title-based keywords
        title_words = [w.lower() for w in re.findall(r'\b[a-z]{4,}\b', self.title.lower())]
        keywords.extend(title_words[:2])

        return keywords

    def _get_keyword_tips(self, genre):
        """Get genre-specific keyword optimization tips"""
        tips = {
            'romance': [
                'Include sub-genre specifics (contemporary, historical, paranormal)',
                'Mention heat level if relevant (sweet, steamy)',
                'Add tropes (enemies to lovers, second chance, fake relationship)'
            ],
            'thriller': [
                'Specify thriller type (psychological, legal, medical)',
                'Include setting if unique (Nordic noir, Southern gothic)',
                'Mention protagonist type (detective, lawyer, journalist)'
            ],
            'fantasy': [
                'Specify fantasy type (epic, urban, dark)',
                'Include magical elements (dragons, wizards, fae)',
                'Mention world-building elements (kingdoms, magic systems)'
            ],
            'self-help': [
                'Focus on specific transformation (productivity, mindfulness, habits)',
                'Include target audience (entrepreneurs, parents, students)',
                'Mention methodology if applicable (workbook, journal, guide)'
            ]
        }

        return tips.get(genre, [
            'Use specific, searchable terms',
            'Include your target audience',
            'Add relevant sub-categories'
        ])


class CategoryRecommender:
    """BISAC category recommendation system"""

    # Simplified BISAC categories (in reality, there are 3000+)
    BISAC_CATEGORIES = {
        'FICTION': {
            'Romance': ['Contemporary', 'Historical', 'Paranormal', 'Suspense', 'Western'],
            'Thriller': ['Psychological', 'Legal', 'Medical', 'Political', 'Espionage'],
            'Fantasy': ['Epic', 'Urban', 'Historical', 'Paranormal', 'Dark'],
            'Mystery & Detective': ['Cozy', 'Police Procedural', 'Private Investigator', 'Historical'],
            'Science Fiction': ['Space Opera', 'Cyberpunk', 'Time Travel', 'Dystopian'],
            'Literary': ['General', 'Coming of Age', 'Family Life', 'Women'],
            'Horror': ['General', 'Occult & Supernatural', 'Vampires']
        },
        'NON-FICTION': {
            'Self-Help': ['Personal Growth', 'Success', 'Motivational', 'Creativity'],
            'Business & Economics': ['Entrepreneurship', 'Marketing', 'Leadership', 'Personal Finance'],
            'Biography & Autobiography': ['Personal Memoirs', 'Literary', 'Business'],
            'Health & Fitness': ['Diet', 'Exercise', 'Mental Health', 'Wellness'],
            'Psychology': ['General', 'Personality', 'Cognitive Psychology'],
            'Religion & Spirituality': ['Inspiration', 'Meditation', 'Prayer']
        }
    }

    def recommend(self, genre, themes, title):
        """Recommend BISAC categories"""
        recommendations = []

        # Determine if fiction or non-fiction
        is_fiction = self._is_fiction(genre, themes, title)
        main_category = 'FICTION' if is_fiction else 'NON-FICTION'

        # Find best matching subcategories
        categories = self.BISAC_CATEGORIES[main_category]

        # Score each category
        category_scores = {}
        for category, subcats in categories.items():
            score = self._score_category(category, subcats, genre, themes, title)
            category_scores[category] = score

        # Get top 2 categories
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

        for category, score in sorted_categories[:2]:
            subcats = categories[category]
            best_subcat = self._find_best_subcategory(subcats, themes, title)

            recommendations.append({
                'main': main_category,
                'category': category,
                'subcategory': best_subcat,
                'full_path': f"{main_category} > {category} > {best_subcat}",
                'confidence': min(100, score * 10)
            })

        return recommendations

    def _is_fiction(self, genre, themes, title):
        """Determine if book is fiction or non-fiction"""
        fiction_indicators = ['story', 'novel', 'tale', 'romance', 'fantasy', 'thriller', 'mystery']
        nonfiction_indicators = ['guide', 'how', 'learn', 'improve', 'understand', 'master', 'success']

        text = f"{genre} {' '.join(themes)} {title}".lower()

        fiction_score = sum(text.count(word) for word in fiction_indicators)
        nonfiction_score = sum(text.count(word) for word in nonfiction_indicators)

        return fiction_score >= nonfiction_score

    def _score_category(self, category, subcats, genre, themes, title):
        """Score how well a category matches the book"""
        text = f"{genre} {' '.join(themes)} {title}".lower()
        category_text = f"{category} {' '.join(subcats)}".lower()

        score = 0
        for word in category_text.split():
            if word in text:
                score += 1

        return score

    def _find_best_subcategory(self, subcats, themes, title):
        """Find best matching subcategory"""
        text = f"{' '.join(themes)} {title}".lower()

        best_subcat = subcats[0]
        best_score = 0

        for subcat in subcats:
            score = sum(word.lower() in text for word in subcat.split())
            if score > best_score:
                best_score = score
                best_subcat = subcat

        return best_subcat


class DescriptionOptimizer:
    """Optimize book description for KDP"""

    def optimize(self, raw_description, genre, keywords):
        """Generate optimized HTML-formatted description"""

        # Clean and structure description
        paragraphs = [p.strip() for p in raw_description.split('\n') if p.strip()]

        # Generate optimized version
        optimized = self._format_description(paragraphs, genre, keywords)

        return {
            'html': optimized,
            'plain': raw_description,
            'character_count': len(optimized),
            'tips': self._get_description_tips(genre)
        }

    def _format_description(self, paragraphs, genre, keywords):
        """Format description with HTML"""
        html_parts = []

        # Strong opening hook
        if paragraphs:
            html_parts.append(f"<b>{paragraphs[0]}</b>")
            paragraphs = paragraphs[1:]

        # Add body paragraphs
        for para in paragraphs[:3]:  # Max 3-4 paragraphs
            html_parts.append(f"<p>{para}</p>")

        # Add bullet points if beneficial
        if len(keywords) > 3:
            html_parts.append("<p><b>In this book, you'll discover:</b></p>")
            html_parts.append("<ul>")
            for keyword in keywords[:4]:
                html_parts.append(f"<li>{keyword.capitalize()}</li>")
            html_parts.append("</ul>")

        return '\n'.join(html_parts)

    def _get_description_tips(self, genre):
        """Get genre-specific description tips"""
        return [
            '✓ Start with a hook in the first sentence',
            '✓ Keep it under 4000 characters',
            '✓ Use HTML formatting (<b>, <i>, <ul>, <li>)',
            '✓ Include keywords naturally',
            '✓ End with a call-to-action',
            f'✓ For {genre}: Focus on what makes your book unique'
        ]


class SimpleCoverGenerator:
    """Generate simple cover designs"""

    # Pre-defined color schemes
    COLOR_SCHEMES = {
        'romance': [('#FFE5E5', '#FF69B4', '#8B0000')],  # Pink/Red
        'thriller': [('#000000', '#FF0000', '#FFFFFF')],  # Black/Red/White
        'fantasy': [('#4A0080', '#FFD700', '#000000')],  # Purple/Gold
        'self-help': [('#00A8E8', '#FFFFFF', '#003459')],  # Blue professional
        'business': [('#1A365D', '#F97316', '#FFFFFF')],  # Deep blue/Orange
    }

    def generate_cover(self, title, author, genre='literary', subtitle=''):
        """Generate a simple cover design"""

        # Create image (1600x2400 for KDP)
        width, height = 1600, 2400

        # Get color scheme
        colors = self.COLOR_SCHEMES.get(genre, [('#1A365D', '#F97316', '#FFFFFF')])[0]
        bg_color, accent_color, text_color = colors

        # Create image
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Georgia.ttf', 120)
            author_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Georgia.ttf', 60)
            subtitle_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Georgia.ttf', 50)
        except:
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Draw accent bar
        bar_height = 200
        draw.rectangle([(0, height // 2 - bar_height // 2), (width, height // 2 + bar_height // 2)],
                      fill=accent_color)

        # Draw title (centered)
        title_words = title.upper().split()
        y_offset = height // 3
        for word in title_words:
            bbox = draw.textbbox((0, 0), word, font=title_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y_offset), word, fill=text_color, font=title_font)
            y_offset += 140

        # Draw subtitle if provided
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y_offset + 30), subtitle, fill=text_color, font=subtitle_font)

        # Draw author name
        bbox = draw.textbbox((0, 0), author.upper(), font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = height - 200
        draw.text((x, y), author.upper(), fill=text_color, font=author_font)

        return img

    def save_cover(self, img, output_path):
        """Save cover image"""
        img.save(output_path, 'PNG', dpi=(300, 300))
        return output_path


def generate_premium_package(doc_path, title, author, description=''):
    """Generate complete premium package"""

    # Keyword research
    keyword_tool = KeywordResearcher(doc_path, title, description)
    keyword_results = keyword_tool.analyze()

    # Category recommendations
    category_tool = CategoryRecommender()
    categories = category_tool.recommend(
        keyword_results['genre'],
        keyword_results['themes'],
        title
    )

    # Description optimizer
    desc_tool = DescriptionOptimizer()
    description_results = desc_tool.optimize(
        description or "Your book description here.",
        keyword_results['genre'],
        keyword_results['recommended_7']
    )

    # Cover generator
    cover_tool = SimpleCoverGenerator()
    cover_img = cover_tool.generate_cover(
        title,
        author,
        keyword_results['genre']
    )

    return {
        'keywords': keyword_results,
        'categories': categories,
        'description': description_results,
        'cover_image': cover_img
    }
