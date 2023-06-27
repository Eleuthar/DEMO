from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from .models import Question, Option


def index(request):
    questionz = Question.objects.order_by("-pub_date")[:5]
    context = {"questionz": questionz}
    return render(request, "polls/index.html", context)


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    # optionz = question.option_set.all()
    context = {'question': question}
    return render(request, "polls/detail.html", context)


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        option = question.option_set.get(pk=request.POST['option'])
    except (KeyError, Option.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        option.votes += 1
        option.save()
        return HttpResponseRedirect(reverse("polls:result", args=(question.id,)))


def result(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/result.html", {"question": question})
