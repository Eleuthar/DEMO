from .models import Sport, Market, Selection, Match
from rest_framework.serializers import ModelSerializer


class SportSerializer(ModelSerializer):
    class Meta:
        model = Sport
        fields = ('id', 'name')
    
        
class SelectionSerializer(ModelSerializer):
    class Meta:
        model = Selection
        fields = ('id', 'name', 'oddz')
        
        
class MarketSerializer(ModelSerializer):
    selections = SelectionSerializer(many=True)

    class Meta:
        model = Market
        fields = ('id', 'name', 'selections')
    
        
class MatchListSerializer(ModelSerializer):
    class Meta:
        model = Match
        fields = ('id', 'url', 'name', 'start_time')
    
        
class MatchDetailSerializer(ModelSerializer):
    sport = SportSerializer()
    makert = MarketSerializer()
    
    class Meta:
        model = Match
        fields = ('id', 'url', 'name', 'start_time', 'sport', 'market')
    
    def validate(self, data):
        xss_filter = "<(?:[^>=]|='[^']*'|=\"[^\"]*\"|=[^'\"][^\\s>]*)*>"

        for uzr_input in Meta.fields:
            if re.search('xss_filter', data[uzr_input]):
                raise ValidationError(detail="Invalid input. Try that again and the FBI are on their way!", code=400)

        return data
